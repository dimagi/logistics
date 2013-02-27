from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Sum, Min, Max, Q, F

from dimagi.utils.dates import months_between, first_of_next_month, delta_secs

from rapidsms.contrib.messagelog.models import Message

from logistics.models import SupplyPoint, ProductReport, StockTransaction,\
    ProductStock, Product, StockRequest
from logistics.util import config
from logistics.const import Reports

from warehouse.runner import WarehouseRunner
from warehouse.models import ReportRun

from static.malawi.config import TimeTrackerTypes

from logistics_project.apps.malawi.util import group_for_location, hsas_below,\
    hsa_supply_points_below, facility_supply_points_below, get_supervisors,\
    get_hsa_supervisors, get_in_charge
from logistics_project.apps.malawi.warehouse.models import ReportingRate,\
    ProductAvailabilityData, ProductAvailabilityDataSummary, UserProfileData, \
    TIME_TRACKER_TYPES, TimeTracker, OrderRequest, OrderFulfillment, Alert,\
    CalculatedConsumption, CurrentConsumption, HistoricalStock
from django.core.exceptions import ObjectDoesNotExist


class MalawiWarehouseRunner(WarehouseRunner):
    """
    Malawi's implementation of the warehouse runner. 
    """
    # debug stuff
    skip_hsas = False
    skip_aggregates = False
    skip_reporting_rates = False
    skip_product_availability = False
    skip_lead_times = False
    skip_order_requests = False
    skip_order_fulfillment = False
    skip_profile_data = False
    skip_alerts = False
    skip_consumption = False
    skip_current_consumption = False
    skip_historical_stock = False
    consumption_test_mode = False
    hsa_limit = 0
    
    def cleanup(self, start, end):
        print "Malawi warehouse cleanup!"  
        # TODO: fix this up - currently deletes all records having any data
        # within the period
        ReportRun.objects.filter(start__gte=start, end__lte=end).delete()
        if not self.skip_reporting_rates:
            ReportingRate.objects.filter(date__gte=start, date__lte=end).delete()
        if not self.skip_product_availability:
            ProductAvailabilityData.objects.filter(date__gte=start, date__lte=end).delete()
            ProductAvailabilityDataSummary.objects.filter(date__gte=start, date__lte=end).delete()
        if not self.skip_lead_times:
            TimeTracker.objects.filter(date__gte=start, date__lte=end).delete()
        if not self.skip_order_requests:
            OrderRequest.objects.filter(date__gte=start, date__lte=end).delete()
        if not self.skip_order_fulfillment:
            OrderFulfillment.objects.filter(date__gte=start, date__lte=end).delete()
        if not self.skip_consumption:
            CalculatedConsumption.objects.all().delete()
        if not self.skip_historical_stock:
            HistoricalStock.objects.filter(date__gte=start, date__lte=end).delete()
            
    def generate(self, run_record):
        print "Malawi warehouse generate!"
        
        start = run_record.start
        end = run_record.end
        first_activity = Message.objects.order_by('date')[0].date
        if start < first_activity:
            start = first_activity
        
        # first populate all the warehouse tables for all facilities
        hsas = SupplyPoint.objects.filter(active=True, type__code='hsa').order_by('id')
        if self.hsa_limit:
            hsas = hsas[:self.hsa_limit]
        
        count = len(hsas)
        if not self.skip_hsas:
            for i, hsa in enumerate(hsas):
                # process all the hsa-level warehouse tables
                is_em_group = (group_for_location(hsa.location) == config.Groups.EM)
                products_managed = set([c.pk for c in hsa.commodities_stocked()])
                        
                print "processing hsa %s (%s) (%s of %s)" % (hsa.name, str(hsa.id), i, count)
                
                if not self.skip_current_consumption:
                    update_current_consumption(hsa)
                
                for year, month in months_between(start, end):
                    window_date = datetime(year, month, 1)
                    next_window_date = first_of_next_month(window_date)
                    period_start = max(window_date, start)
                    period_end = min(next_window_date, end)
                    
                    # NOTE: the only reason the breakdowns below are functions 
                    # is for future refactoring purposes, and the only reason 
                    # they are declared here is because of the current heavy 
                    # use of closures.
                    def _update_reporting_rate():
                        """
                        Process reports (on time versus late, versus at 
                        all and completeness)
                        """
                        late_cutoff = window_date + timedelta(days=settings.LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT)
                        
                        reports_in_range = ProductReport.objects.filter\
                            (supply_point=hsa, report_type__code=Reports.SOH,
                             report_date__gte=period_start, report_date__lte=period_end)
                        period_rr = ReportingRate.objects.get_or_create\
                            (supply_point=hsa, date=window_date)[0]
                        period_rr.total = 1
                        period_rr.reported = 1 if reports_in_range else period_rr.reported
                        # for the em group "on time" is meaningful, for the ept group 
                        # they are always considered "on time" 
                        if reports_in_range and is_em_group:
                            first_report_date = reports_in_range.order_by('report_date')[0].report_date
                            period_rr.on_time = first_report_date <= late_cutoff or period_rr.on_time
                        else:
                            period_rr.on_time = period_rr.on_time if is_em_group else period_rr.reported
                        
                        if not period_rr.complete:
                            # check for completeness (only if not already deemed complete)
                            # unfortunately, we have to walk all avaialable 
                            # transactions in the period every month 
                            # in order to do this correctly.
                            this_months_reports = ProductReport.objects.filter\
                                (supply_point=hsa, report_type__code=Reports.SOH,
                                 report_date__gte=window_date, report_date__lte=period_end)
                            
                            found = set(this_months_reports.values_list("product", flat=True).distinct())
                            period_rr.complete = 0 if found and (products_managed - found) else \
                                (1 if found else 0)
                        
                        period_rr.save()
                    
                    def _update_product_availability():
                        """
                        Compute ProductAvailabilityData
                        """
                        # NOTE: this currently calculates everything on a 
                        # per-month basis. if it is determined that we only
                        # need current information, the models can be cleaned
                        # up a bit
                        for p in Product.objects.all():
                            product_data, created = ProductAvailabilityData.objects.get_or_create\
                                (product=p, supply_point=hsa, 
                                 date=window_date)
                            
                            if created:
                                # initally assume we have no data on anything
                                product_data.without_data = 1
                            
                            transactions = StockTransaction.objects.filter\
                                (supply_point=hsa, product=p,
                                 date__gte=period_start, 
                                 date__lt=period_end).order_by('-date')
                            product_data.total = 1
                            product_data.managed = 1 if hsa.supplies(p) else 0
                            if transactions:
                                trans = transactions[0]
                                product_stock = ProductStock.objects.get\
                                    (product=trans.product, supply_point=hsa)
                                
                                product_data.without_data = 0
                                if trans.ending_balance <= 0:
                                    product_data.without_stock = 1
                                    product_data.with_stock = 0
                                    product_data.under_stock = 0
                                    product_data.over_stock = 0
                                else: 
                                    product_data.without_stock = 0
                                    product_data.with_stock = 1
                                    if product_stock.emergency_reorder_level and \
                                         trans.ending_balance <= product_stock.emergency_reorder_level:
                                        product_data.emergency_stock = 1
                                    if product_stock.reorder_level and \
                                         trans.ending_balance <= product_stock.reorder_level:
                                        product_data.under_stock = 1
                                        product_data.over_stock = 0
                                    elif product_stock.maximum_level and \
                                         trans.ending_balance > product_stock.maximum_level:
                                        product_data.under_stock = 0
                                        product_data.over_stock = 1
                                    else:
                                        product_data.under_stock = 0
                                        product_data.over_stock = 0
                                
                                product_data.good_stock = product_data.with_stock - \
                                    (product_data.under_stock + product_data.over_stock)
                                assert product_data.good_stock in (0, 1)
                                
                            product_data.set_managed_attributes()
                            product_data.save()
                            
                        # update the summary data
                        product_summary = ProductAvailabilityDataSummary.objects.get_or_create\
                            (supply_point=hsa, 
                             date=window_date)[0]
                        product_summary.total = 1
                        
                        if hsa.commodities_stocked():
                            product_summary.any_managed = 1
                            agg_results = ProductAvailabilityData.objects.filter\
                                (supply_point=hsa, date=window_date, 
                                 managed=1).aggregate\
                                 (*[Max("managed_and_%s" % c) for c in \
                                    ProductAvailabilityData.STOCK_CATEGORIES])
                            for c in ProductAvailabilityData.STOCK_CATEGORIES:
                                setattr(product_summary, "any_%s" % c, 
                                        agg_results["managed_and_%s__max" % c])
                                assert getattr(product_summary, "any_%s" % c) <= 1
                        else:
                            product_summary.any_managed = 0
                            for c in ProductAvailabilityData.STOCK_CATEGORIES:
                                setattr(product_summary, "any_%s" % c, 0)
                        
                        product_summary.save()                            
                    
                    def _update_lead_times():
                        # ord-ready
                        
                        # NOTE: the existing code currently also removes 
                        # status 'canceled'. Is this necessary?
                        requests_in_range = StockRequest.objects.filter(\
                            responded_on__gte=period_start,
                            responded_on__lt=period_end,
                            supply_point=hsa
                        ).exclude(requested_on=None)
                        or_tt = TimeTracker.objects.get_or_create\
                            (supply_point=hsa, date=window_date,
                             type=TimeTrackerTypes.ORD_READY)[0]
                        for r in requests_in_range:
                            lt = delta_secs(r.responded_on - r.requested_on)
                            or_tt.time_in_seconds += lt
                            or_tt.total += 1
                        or_tt.save()
                        
                        # ready-receieved
                        requests_in_range = StockRequest.objects.filter(\
                            received_on__gte=period_start,
                            received_on__lt=period_end,
                            supply_point=hsa
                        ).exclude(responded_on=None)
                        rr_tt = TimeTracker.objects.get_or_create\
                            (supply_point=hsa, date=window_date,
                             type=TimeTrackerTypes.READY_REC)[0]
                        for r in requests_in_range:
                            lt = delta_secs(r.received_on - r.responded_on)
                            rr_tt.time_in_seconds += lt
                            rr_tt.total += 1
                        rr_tt.save()
                    
                    def _update_order_requests():
                        requests_in_range = StockRequest.objects.filter(\
                            requested_on__gte=period_start,
                            requested_on__lt=period_end,
                            supply_point=hsa
                        )
                        for p in Product.objects.all():
                            ord_req = OrderRequest.objects.get_or_create\
                                (supply_point=hsa, date=window_date, product=p)[0]
                            ord_req.total += requests_in_range.filter(product=p).count()
                            ord_req.emergency += requests_in_range.filter\
                                (product=p, is_emergency=True).count()
                            ord_req.save()
                            
                    def _update_order_fulfillment():
                        requests_in_range = StockRequest.objects.filter(\
                            received_on__gte=period_start,
                            received_on__lt=period_end,
                            supply_point=hsa,
                        ).exclude(Q(amount_requested=None) | Q(amount_received=None))
                        for p in Product.objects.all():
                            order_fulfill = OrderFulfillment.objects.get_or_create\
                                (supply_point=hsa, date=window_date, product=p)[0]
                            for r in requests_in_range.filter(product=p):
                                order_fulfill.total += 1
                                order_fulfill.quantity_requested += r.amount_requested
                                order_fulfill.quantity_received += r.amount_received
                            if requests_in_range.count():
                                order_fulfill.save()
                    
                    def _update_consumption():
                        for p in Product.objects.all():
                            c = CalculatedConsumption.objects.get_or_create\
                                (supply_point=hsa, date=window_date, product=p)[0]
                            
                            start_time = max(hsa.created_at, window_date)
                            if start_time < period_end and hsa.supplies(p):
                                assert start_time.year == window_date.year 
                                assert start_time.month == window_date.month
                                c.time_needing_data = delta_secs(period_end - start_time)
                                c.save()
                            transactions = StockTransaction.objects.filter\
                                (supply_point=hsa, product=p,
                                 date__gte=period_start, 
                                 date__lt=period_end).order_by('date')
                            update_consumption_values(transactions)
                            
                    def _update_historical_stock():
                        # set the historical stock values to the last report before 
                        # the end of the period (even if it's not in the period)
                        for p in Product.objects.all():
                            hs = HistoricalStock.objects.get_or_create\
                                (supply_point=hsa, date=window_date, product=p)[0]
                            
                            transactions = StockTransaction.objects.filter\
                                (supply_point=hsa, product=p,
                                 date__lt=period_end).order_by('-date')
                            
                            hs.total = 1
                            if transactions.count():
                                hs.stock = transactions[0].ending_balance
                            hs.save()
                        
                    
                    if not self.skip_reporting_rates:
                        _update_reporting_rate()
                    if not self.skip_product_availability:
                        _update_product_availability()
                    if not self.skip_lead_times:
                        _update_lead_times()
                    if not self.skip_order_requests:
                        _update_order_requests()
                    if not self.skip_order_fulfillment:
                        _update_order_fulfillment()
                    if not self.skip_consumption:
                        _update_consumption()
                    if not self.skip_historical_stock:
                        _update_historical_stock()
        
        if not self.skip_consumption:
            # any consumption value that was touched potentially needs to have its
            # time_needing_data updated
            for c in CalculatedConsumption.objects.filter(update_date__gte=run_record.start_run):
                # if they supply the product it is already set based on above
                if not c.supply_point.supplies(c.product):
                    c.time_needing_data = c.time_with_data
                    c.save()
                
                
        # rollup aggregates
        non_hsas = SupplyPoint.objects.filter(active=True)\
            .exclude(type__code='hsa').order_by('id')
        # national only
        # non_hsas = SupplyPoint.objects.filter(active=True, type__code='c')
        all_products = Product.objects.all()
        if not self.skip_aggregates: 
            
            for place in non_hsas:
                print "processing non-hsa %s (%s)" % (place.name, str(place.id))
                relevant_hsas = hsa_supply_points_below(place.location)
                
                if not self.skip_current_consumption:
                    for p in all_products:
                        _aggregate_raw(CurrentConsumption, place, relevant_hsas,
                                       fields=["total", "current_daily_consumption", "stock_on_hand"], 
                                       additonal_query_params={"product": p})
                        
                for year, month in months_between(start, end):
                    window_date = datetime(year, month, 1)
                    if not self.skip_reporting_rates:
                        _aggregate(ReportingRate, window_date, place, relevant_hsas, 
                                   fields=['total', 'reported', 'on_time', 'complete'])
                    if not self.skip_product_availability:
                        for p in all_products:
                            _aggregate(ProductAvailabilityData, window_date, place, relevant_hsas,
                                       fields=['total', 'managed'] + \
                                            ProductAvailabilityData.STOCK_CATEGORIES + \
                                            ["managed_and_%s" % c for c in ProductAvailabilityData.STOCK_CATEGORIES],
                                       additonal_query_params={"product": p})
                        _aggregate(ProductAvailabilityDataSummary, window_date, place, 
                                   relevant_hsas, fields=['total', 'any_managed'] + \
                                   ["any_%s" % c for c in ProductAvailabilityData.STOCK_CATEGORIES])
                    if not self.skip_lead_times:
                        for code, name in TIME_TRACKER_TYPES:
                            _aggregate(TimeTracker, window_date, place, relevant_hsas,
                                       fields=['total', 'time_in_seconds'],
                                       additonal_query_params={"type": code})
                    if not self.skip_order_requests:
                        for p in all_products:
                            _aggregate(OrderRequest, window_date, place, relevant_hsas,
                                       fields=['total', 'emergency'],
                                       additonal_query_params={"product": p})
                    if not self.skip_order_fulfillment:
                        for p in all_products:
                            _aggregate(OrderFulfillment, window_date, place, relevant_hsas,
                                       fields=['total', 'quantity_requested', 'quantity_received'],
                                       additonal_query_params={"product": p})
                    
                    if not self.skip_consumption and self.consumption_test_mode:
                        for p in all_products:
                            # NOTE: this is not correct, but is for testing / iteration
                            _aggregate(CalculatedConsumption, window_date, place, relevant_hsas,
                                       fields=['calculated_consumption', 
                                               'time_stocked_out',
                                               'time_with_data',
                                               'time_needing_data'],
                                       additonal_query_params={"product": p})
                    
                    if not self.skip_historical_stock:
                        for p in all_products:
                            _aggregate(HistoricalStock, window_date, place, relevant_hsas,
                                       fields=["total", "stock"],
                                       additonal_query_params={"product": p})
                        
                
                if not self.skip_consumption and not self.consumption_test_mode:
                    for p in all_products:
                        # We have to use a special date range filter here, 
                        # since the warehouse can update historical values
                        # outside the range we are looking at
                        agg = CalculatedConsumption.objects.filter(
                            update_date__gte=run_record.start_run,
                            supply_point__in=hsas
                        ).aggregate(Min('date'))
                        new_start = agg.get('date__min', None)
                        if new_start:
                            assert new_start <= end
                            for year, month in months_between(new_start, end):
                                window_date = datetime(year, month, 1)
                                _aggregate(CalculatedConsumption, window_date, place, relevant_hsas,
                                   fields=['calculated_consumption', 
                                           'time_stocked_out',
                                           'time_with_data',
                                           'time_needing_data'],
                                   additonal_query_params={"product": p})
                        
                            
                        
                        
        
        # run user profile summary
        if not self.skip_profile_data: 
            update_user_profile_data()

        # run alerts
        if not self.skip_alerts:
            update_alerts()


def _aggregate_raw(modelclass, supply_point, base_supply_points, fields,
               additonal_query_params={}):
    """
    Aggregate an instance of modelclass, by summing up all of the fields for
    any matching models found in the same date range in the base_supply_points.
    
    Returns the updated reporting model class.
    """
    period_instance = modelclass.objects.get_or_create\
        (supply_point=supply_point, **additonal_query_params)[0]
    children_qs = modelclass.objects.filter\
        (supply_point__in=base_supply_points, **additonal_query_params)
         
    totals = children_qs.aggregate(*[Sum(f) for f in fields])
    [setattr(period_instance, f, totals["%s__sum" % f] or 0) for f in fields]
    period_instance.save()
    return period_instance

def _aggregate(modelclass, window_date, supply_point, base_supply_points, fields,
               additonal_query_params={}):
    """
    Aggregate an instance of modelclass, by summing up all of the fields for
    any matching models found in the same date range in the base_supply_points.
    
    Returns the updated reporting model class.
    """
    additonal_query_params["date"] = window_date
    return _aggregate_raw(modelclass, supply_point, base_supply_points, fields, 
                          additonal_query_params)
    
def update_current_consumption(hsa):
    """
    Update the actual consumption data
    """
    for p in Product.objects.all():
        
        consumption = CurrentConsumption.objects.get_or_create\
            (supply_point=hsa, product=p)[0]
        consumption.total = 1
        try:
            ps = ProductStock.objects.get(supply_point=hsa,
                                          product=p)
            consumption.current_daily_consumption = ps.daily_consumption or 0
            consumption.stock_on_hand = ps.quantity or 0
        except ObjectDoesNotExist:
            consumption.current_daily_consumption = 0
            consumption.stock_on_hand = 0
        consumption.save()
    
    
def update_consumption_values(transactions):
    """
    Update the consumption calculations
    """
    # grab all the transactions in the period, plus 
    # the one immediately before the first one if there is one
    
    # walk through them, determining consumption amounts 
    # between them.
    # for each delta, compute its total effect on consumption
    # throwing away anomalous values like SOH increasing
    if transactions.count():
        to_process = list(transactions)
        start_t = to_process[0].previous_transaction()
        if start_t:
            to_process.insert(0, start_t)
        if len(to_process) > 1:
            for i in range(len(to_process) - 1):
                start, end = to_process[i:i+2]
                assert start.supply_point == end.supply_point
                assert start.product == end.product
                assert start.date <= end.date
                delta = end.ending_balance - start.ending_balance
                # assert delta == end.quantity

                total_timedelta = end.date - start.date
                for year, month in months_between(start.date, end.date):
                    window_date = datetime(year, month, 1)
                    next_window_date = first_of_next_month(window_date)
                    start_date = max(window_date, start.date)
                    end_date = min(next_window_date, end.date)
                    secs_in_window = delta_secs(end_date-start_date)
                    proportion_in_window = secs_in_window / (delta_secs(total_timedelta)) \
                        if secs_in_window else 0
                    assert proportion_in_window <= 1
                    c = CalculatedConsumption.objects.get_or_create\
                        (supply_point=start.supply_point, date=window_date, 
                         product=start.product)[0]
                    if delta < 0:
                        # update the consumption by adding the proportion in the window
                        c.calculated_consumption += float(abs(delta)) * proportion_in_window
                    
                    # only count time with data if the balance went down or 
                    # stayed the same, or was a receipt.
                    # otherwise it's anomalous data.
                    if delta <= 0 or end.product_report.report_type.code == Reports.REC:
                        c.time_with_data += secs_in_window
                    
                    if start.ending_balance == 0:
                        c.time_stocked_out += secs_in_window
                    
                    c.save()

def update_user_profile_data():
    print "updating user profile data"
    for supply_point in SupplyPoint.objects.filter(active=True):
        new_obj = UserProfileData.objects.get_or_create(supply_point=supply_point)[0]

        new_obj.facility_children = facility_supply_points_below(supply_point.location).count()
        new_obj.hsa_children = hsa_supply_points_below(supply_point.location).count()

        new_obj.in_charge = get_in_charge(supply_point).count()
        new_obj.hsa_supervisors = get_hsa_supervisors(supply_point).count()
        new_obj.supervisor_contacts = get_supervisors(supply_point).count()
        new_obj.contacts = supply_point.active_contact_set.count()

        new_obj.contact_info = ''
        if supply_point.type.code == "hsa":
            if supply_point.contacts().count():
                contact = supply_point.contacts()[0]
                if contact.default_connection:
                    new_obj.contact_info = contact.default_connection.identity
                
                msgs = Message.objects.filter(direction='I', contact=contact).order_by('-date')
                if msgs.count() > 0:
                    new_obj.last_message = msgs[0]

        new_obj.products_managed = ''
        for product in supply_point.commodities_stocked():
            new_obj.products_managed += ' %s' % product.sms_code

        new_obj.save()
    return True

def update_alerts():
    print "updating alerts"

    for sp in SupplyPoint.objects.all():
        new_obj = Alert.objects.get_or_create(supply_point=sp)[0]

        hsas = hsa_supply_points_below(sp.location)
        new_obj.num_hsas = hsas.count()

        new_obj.without_products_managed = 0
        new_obj.total_requests = 0
        new_obj.have_stockouts = 0
        new_obj.eo_total = 0
        new_obj.eo_with_resupply = 0
        new_obj.eo_without_resupply = 0
        new_obj.reporting_receipts = 0
        new_obj.order_readys = 0
        for hsa in hsas:
            new_obj.without_products_managed += 1 if hsa.commodities_stocked().count() == 0 else 0
            sreq = StockRequest.objects.filter(supply_point=hsa)
            new_obj.total_requests += 1 if sreq.count() > 0 else 0
            sreq = StockRequest.objects.filter(supply_point=hsa, balance=0)
            new_obj.have_stockouts += 1 if sreq.count() > 0 else 0
            sreq = StockRequest.objects.filter(supply_point=hsa, is_emergency=True)
            new_obj.eo_total += 1 if sreq.count() > 0 else 0
            sreq = StockRequest.objects.filter(supply_point=hsa, is_emergency=True,\
                    amount_received__gt=0, balance__lt=F('product__emergency_order_level'))
            new_obj.eo_with_resupply += 1 if sreq.count() > 0 else 0
            sreq = StockRequest.pending_requests().filter(supply_point=hsa, is_emergency=True)
            new_obj.eo_without_resupply += 1 if sreq.count() > 0 else 0
            sreq = StockRequest.objects.filter(supply_point=hsa)\
                .exclude(received_on=None, responded_on=None, response_status='stocked_out')
            new_obj.reporting_receipts += 1 if sreq.count() > 0 else 0
            sreq = StockRequest.objects.filter(supply_point=hsa)\
                .exclude(responded_on=None, response_status='stocked_out')
            new_obj.order_readys += 1 if sreq.count() > 0 else 0
        
        new_obj.save()
    return True
