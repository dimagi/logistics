from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Sum, Min, Max, Q, F

from dimagi.utils.dates import months_between, first_of_next_month, delta_secs

from rapidsms.contrib.messagelog.models import Message

from logistics.models import SupplyPoint, ProductReport, StockTransaction,\
    ProductStock, Product, StockRequest, StockRequestStatus
from logistics.const import Reports
from logistics.warehouse_models import SupplyPointWarehouseRecord

from warehouse.runner import WarehouseRunner
from warehouse.models import ReportRun

from static.malawi.config import TimeTrackerTypes, SupplyPointCodes, BaseLevel

from logistics_project.apps.malawi.util import (hsa_supply_points_below, get_country_sp,
    get_managed_product_ids, filter_district_queryset_for_epi)
from logistics_project.apps.malawi.warehouse.models import ReportingRate,\
    ProductAvailabilityData, ProductAvailabilityDataSummary, \
    TIME_TRACKER_TYPES, TimeTracker, OrderRequest, OrderFulfillment, Alert,\
    CalculatedConsumption, CurrentConsumption, HistoricalStock
from django.core.exceptions import ObjectDoesNotExist


class ReportPeriod(object):

    def __init__(self, supply_point, window_date, start, end):
        self.supply_point = supply_point
        self.window_date = window_date
        self.start = start
        self.end = end
        self.next_window_date = first_of_next_month(self.window_date)
        self.period_start = max(window_date, start)
        self.period_end = min(self.next_window_date, end)


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
    skip_alerts = False
    skip_consumption = False
    skip_current_consumption = False
    skip_historical_stock = False
    consumption_test_mode = False
    hsa_limit = 0
    facility_limit = 0
    agg_limit_per_type = 0

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
        """
        Note that no warehouse data is stored at the zone level throughout
        the entire warehouse process since reporting on zone is not a
        requirement.
        """
        print "Malawi warehouse generate!"

        start = run_record.start
        end = run_record.end
        first_activity = Message.objects.order_by('date')[0].date
        if start < first_activity:
            start = first_activity
        
        # first populate all the warehouse tables for all hsas
        hsas = SupplyPoint.objects.filter(active=True, type__code=SupplyPointCodes.HSA).order_by('id')
        if self.hsa_limit:
            hsas = hsas[:self.hsa_limit]
        
        count = len(hsas)
        if not self.skip_hsas:
            products = get_products(BaseLevel.HSA)
            for i, hsa in enumerate(hsas):
                # process all the hsa-level warehouse tables
                print "processing hsa %s (%s) (%s of %s)" % (hsa.name, str(hsa.id), i, count)
                self.update_base_level_data(hsa, start, end, products)

        if settings.ENABLE_FACILITY_WORKFLOWS:
            print 'processing facility data'
            products = get_products(BaseLevel.FACILITY)
            facilities = SupplyPoint.objects.filter(active=True, type__code=SupplyPointCodes.FACILITY).order_by('id')
            if self.facility_limit:
                facilities = facilities[:self.facility_limit]
            for i, facility in enumerate(facilities):
                print "processing facility %s (%s) (%s of %s)" % (facility.name, str(facility.id), i, count)
                self.update_base_level_data(facility, start, end, products, base_level=BaseLevel.FACILITY)

        if not self.skip_consumption:
            update_consumption_times(run_record.start_run)

        # rollup aggregates
        if not self.skip_aggregates:
            self.aggregate_data(start, end, run_record, BaseLevel.HSA)

            if settings.ENABLE_FACILITY_WORKFLOWS:
                self.aggregate_data(start, end, run_record, BaseLevel.FACILITY)

        # run alerts
        if not self.skip_alerts:
            update_alerts(hsas)

        update_historical_data()

    def aggregate_data(self, start, end, run_record, base_level):
        products = get_products(base_level)
        for agg_type_code, agg_type_name in aggregate_types_in_order(base_level):
            supply_points = SupplyPoint.objects.filter(active=True).filter(type__code=agg_type_code).order_by('id')
            print 'aggregating data at level %s for base level %s' % (agg_type_name, base_level)

            if self.agg_limit_per_type:
                supply_points = supply_points[:self.agg_limit_per_type]

            supply_points_count = supply_points.count()
            for i, supply_point in enumerate(supply_points):
                print "processing %s %s (%s) (%s/%s)" % (
                    agg_type_name,
                    supply_point.name,
                    supply_point.id,
                    i,
                    supply_points_count
                )

                self.update_aggregated_data(
                    supply_point,
                    start,
                    end,
                    run_record.start_run,
                    all_products=products,
                    base_level=base_level
                )

    def update_base_level_data(self, supply_point, start, end, all_products=None, base_level=BaseLevel.HSA):
        base_level_is_hsa = (base_level == BaseLevel.HSA)
        all_products = all_products or get_products(base_level)
        products_managed = get_managed_product_ids(supply_point, base_level)

        if not self.skip_current_consumption:
            update_current_consumption(supply_point, base_level)

        for year, month in months_between(start, end):
            report_period = ReportPeriod(supply_point, datetime(year, month, 1), start, end)

            if not self.skip_reporting_rates:
                _update_reporting_rate(supply_point, report_period, products_managed, base_level)
            if not self.skip_product_availability:
                _update_product_availability(supply_point, report_period, all_products, products_managed, base_level)
            if not self.skip_lead_times and base_level_is_hsa:
                _update_lead_times(supply_point, report_period)
            if not self.skip_order_requests and base_level_is_hsa:
                _update_order_requests(supply_point, report_period, all_products)
            if not self.skip_order_fulfillment and base_level_is_hsa:
                _update_order_fulfillment(supply_point, report_period, all_products)
            if not self.skip_consumption:
                update_consumption(report_period, base_level, products_managed=products_managed)
            if not self.skip_historical_stock:
                _update_historical_stock(supply_point, report_period, all_products)

    def update_aggregated_data(self, supply_point, start, end, since, all_products=None, base_level=BaseLevel.HSA):
        base_level_is_hsa = (base_level == BaseLevel.HSA)
        all_products = all_products or get_products(base_level)
        relevant_children = proper_children(supply_point)

        if base_level == BaseLevel.FACILITY and supply_point.type_id == SupplyPointCodes.COUNTRY:
            # For EPI, only aggregate national data over participating districts.
            # This makes a difference for models that track total counts, like ReportingRate.
            relevant_children = filter_district_queryset_for_epi(relevant_children)

        if not self.skip_current_consumption:
            for p in all_products:
                _aggregate_raw(CurrentConsumption, supply_point, relevant_children,
                               fields=["total", "current_daily_consumption", "stock_on_hand"],
                               additonal_query_params={"product": p})

        for year, month in months_between(start, end):
            window_date = datetime(year, month, 1)
            if not self.skip_reporting_rates:
                _aggregate(ReportingRate, window_date, supply_point, relevant_children,
                           fields=['total', 'reported', 'on_time', 'complete'],
                           additonal_query_params={'base_level': base_level})

            if not self.skip_product_availability:
                for p in all_products:
                    _aggregate(ProductAvailabilityData, window_date, supply_point, relevant_children,
                               fields=['total', 'managed'] + \
                                    ProductAvailabilityData.STOCK_CATEGORIES + \
                                    ["managed_and_%s" % c for c in ProductAvailabilityData.STOCK_CATEGORIES],
                               additonal_query_params={"product": p})

                _aggregate(ProductAvailabilityDataSummary, window_date, supply_point,
                           relevant_children, fields=['total', 'any_managed'] + \
                           ["any_%s" % c for c in ProductAvailabilityData.STOCK_CATEGORIES],
                           additonal_query_params={'base_level': base_level})

            if not self.skip_lead_times and base_level_is_hsa:
                for code, name in TIME_TRACKER_TYPES:
                    _aggregate(TimeTracker, window_date, supply_point, relevant_children,
                               fields=['total', 'time_in_seconds'],
                               additonal_query_params={"type": code})

            if not self.skip_order_requests and base_level_is_hsa:
                for p in all_products:
                    _aggregate(OrderRequest, window_date, supply_point, relevant_children,
                               fields=['total', 'emergency'],
                               additonal_query_params={"product": p})

            if not self.skip_order_fulfillment and base_level_is_hsa:
                for p in all_products:
                    _aggregate(OrderFulfillment, window_date, supply_point, relevant_children,
                           fields=['total', 'quantity_requested', 'quantity_received'],
                           additonal_query_params={"product": p})

            if not self.skip_consumption and self.consumption_test_mode:
                for p in all_products:
                    # NOTE: this is not correct, but is for testing / iteration
                    _aggregate(CalculatedConsumption, window_date, supply_point, relevant_children,
                               fields=['calculated_consumption',
                                       'time_stocked_out',
                                       'time_with_data',
                                       'time_needing_data'],
                               additonal_query_params={"product": p})

            if not self.skip_historical_stock:
                for p in all_products:
                    _aggregate(HistoricalStock, window_date, supply_point, relevant_children,
                               fields=["total", "stock"],
                               additonal_query_params={"product": p})

        if not self.skip_consumption and not self.consumption_test_mode:
            for p in all_products:
                # We have to use a special date range filter here,
                # since the warehouse can update historical values
                # outside the range we are looking at
                agg = CalculatedConsumption.objects.filter(
                    update_date__gte=since,
                    supply_point__in=relevant_children,
                    product=p
                ).aggregate(Min('date'))
                new_start = agg.get('date__min', None)
                if new_start:
                    assert new_start <= end
                    for year, month in months_between(new_start, end):
                        window_date = datetime(year, month, 1)
                        _aggregate(CalculatedConsumption, window_date, supply_point, relevant_children,
                           fields=['calculated_consumption',
                                   'time_stocked_out',
                                   'time_with_data',
                                   'time_needing_data'],
                           additonal_query_params={"product": p},
                        )


def get_products(base_level):
    return Product.objects.filter(type__base_level=base_level)


def _aggregate_raw(modelclass, supply_point, base_supply_points, fields,
               additonal_query_params=None):
    """
    Aggregate an instance of modelclass, by summing up all of the fields for
    any matching models found in the same date range in the base_supply_points.
    
    Returns the updated reporting model class.
    """
    additonal_query_params = additonal_query_params or {}
    # hack: remove test district users from national level
    if supply_point == get_country_sp():
        base_supply_points = base_supply_points.exclude(code='99')

    period_instance = modelclass.objects.get_or_create\
        (supply_point=supply_point, **additonal_query_params)[0]
    children_qs = modelclass.objects.filter\
        (supply_point__in=base_supply_points, **additonal_query_params)

    totals = children_qs.aggregate(*[Sum(f) for f in fields])
    [setattr(period_instance, f, totals["%s__sum" % f] or 0) for f in fields]
    period_instance.save()
    return period_instance


def _aggregate(modelclass, window_date, supply_point, base_supply_points, fields,
               additonal_query_params=None):
    """
    Aggregate an instance of modelclass, by summing up all of the fields for
    any matching models found in the same date range in the base_supply_points.
    
    Returns the updated reporting model class.
    """
    additonal_query_params = additonal_query_params or {}
    additonal_query_params["date"] = window_date
    return _aggregate_raw(modelclass, supply_point, base_supply_points, fields, 
                          additonal_query_params)

aggregate = _aggregate

def update_current_consumption(supply_point, base_level):
    """
    Update the actual consumption data
    """
    for p in get_products(base_level):
        
        consumption = CurrentConsumption.objects.get_or_create\
            (supply_point=supply_point, product=p)[0]
        consumption.total = 1
        try:
            ps = ProductStock.objects.get(supply_point=supply_point,
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

                    # the number of seconds in this window - should be either the interval
                    # between transactions - or if that interval spans the border of a month
                    # then the interval corresponding to the portion in this month.
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


def update_alerts(hsas):
    non_hsas = (
        SupplyPoint.objects.filter(active=True)
        .exclude(type__code=SupplyPointCodes.HSA)
        .exclude(type__code=SupplyPointCodes.ZONE)
        .order_by('id')
    )
    print "updating alerts"

    def _qs_to_int(queryset):
        return 1 if queryset.count() else 0

    for hsa in hsas:
        base_requests = StockRequest.objects.filter(supply_point=hsa)
        pending_requests = StockRequest.pending_requests().filter(supply_point=hsa)
        emergency_requests = base_requests.filter(is_emergency=True)
        with_resupply = emergency_requests.filter(amount_received__gt=0,
                                                  balance__lt=F('product__emergency_order_level'))
        reporting_receipts = base_requests.exclude(received_on=None, responded_on=None,
                                                   response_status='stocked_out')

        new_obj = Alert.objects.get_or_create(supply_point=hsa)[0]
        new_obj.num_hsas = 1
        new_obj.without_products_managed = 1 if hsa.commodities_stocked().count() == 0 else 0
        new_obj.total_requests = _qs_to_int(base_requests)
        new_obj.have_stockouts = _qs_to_int(base_requests.filter(balance=0))
        new_obj.eo_total = _qs_to_int(emergency_requests)
        new_obj.eo_with_resupply = _qs_to_int(with_resupply)
        new_obj.eo_without_resupply = _qs_to_int(pending_requests.filter(is_emergency=True))
        new_obj.reporting_receipts = _qs_to_int(reporting_receipts)
        new_obj.order_readys = _qs_to_int(base_requests.exclude(responded_on=None, response_status='stocked_out'))
        new_obj.products_requested = _qs_to_int(base_requests.filter(status=StockRequestStatus.REQUESTED))
        new_obj.products_approved = _qs_to_int(base_requests.filter(status=StockRequestStatus.APPROVED))
        new_obj.save()

    for non_hsa in non_hsas:
        relevant_hsas = hsa_supply_points_below(non_hsa.location)
        _aggregate_raw(
            Alert, non_hsa, relevant_hsas,
            fields=[
                "num_hsas",
                "without_products_managed",
                "total_requests",
                "have_stockouts",
                "eo_total",
                "eo_with_resupply",
                "eo_without_resupply",
                "reporting_receipts",
                "order_readys",
                "products_requested",
                "products_approved",
            ],
        )
    return True


def _init_with_base_level(cls, supply_point, date, base_level):
    cls.objects.get_or_create(supply_point=supply_point, date=date, base_level=base_level)


def _init_with_product(cls, supply_point, date, base_level):
    for p in get_products(base_level):
        cls.objects.get_or_create(supply_point=supply_point, date=date, product=p)


def update_consumption(report_period, base_level, products_managed=None):
    if products_managed is None:
        products_managed = get_managed_product_ids(report_period.supply_point, base_level)

    for p in get_products(base_level):
        c = CalculatedConsumption.objects.get_or_create(
            supply_point=report_period.supply_point,
            date=report_period.window_date,
            product=p
        )[0]

        start_time = max(report_period.supply_point.created_at,
                         report_period.window_date)
        if start_time < report_period.period_end and p.pk in products_managed:
            assert start_time.year == report_period.window_date.year
            assert start_time.month == report_period.window_date.month
            c.time_needing_data = delta_secs(report_period.period_end - start_time)
            c.save()
        transactions = StockTransaction.objects.filter(
            supply_point=report_period.supply_point, product=p,
            date__gte=report_period.period_start,
            date__lt=report_period.period_end
        ).order_by('date')
        update_consumption_values(transactions)


def update_consumption_times(since):
    """
    Update the consumption time_with_data values for any supply point / product pairings
    where the supply point doesn't explicitly supply the product.
    """
    # any consumption value that was touched potentially needs to have its
    # time_needing_data updated
    consumptions_to_update = CalculatedConsumption.objects.filter(update_date__gte=since)
    count = consumptions_to_update.count()
    print 'updating %s consumption objects' % count
    for i, c in enumerate(consumptions_to_update.iterator()):
        if i % 500 == 0:
            print '%s/%s consumptions updated' % (i, count)
        # if they supply the product it is already set in update_consumption, above
        if not c.supply_point.supplies(c.product):
            c.time_needing_data = c.time_with_data
            c.save()


def update_historical_data():
    """
    If we don't have a record of this supply point being updated, run
    through all historical data and just fill in with zeros.
    """

    # These models are used by both base levels and have a product attribute
    warehouse_classes_with_product = [
        ProductAvailabilityData,
        CalculatedConsumption,
        HistoricalStock,
    ]

    # These models are used by both base levels and have a base_level attribute
    warehouse_classes_with_base_level = [
        ProductAvailabilityDataSummary,
        ReportingRate,
    ]

    # These models are used by only the HSA base level and have a product attribute
    hsa_only_warehouse_classes_with_product = [
        OrderRequest,
        OrderFulfillment,
    ]

    print 'updating historical data'
    for sp in SupplyPoint.objects.filter(supplypointwarehouserecord__isnull=True).exclude(type__code=SupplyPointCodes.ZONE):
        for year, month in months_between(BaseLevel.HSA_WAREHOUSE_START_DATE, sp.created_at):
            window_date = datetime(year, month, 1)

            for cls in (warehouse_classes_with_product + hsa_only_warehouse_classes_with_product):
                _init_with_product(cls, sp, window_date, BaseLevel.HSA)

            for cls in warehouse_classes_with_base_level:
                _init_with_base_level(cls, sp, window_date, BaseLevel.HSA)

        if settings.ENABLE_FACILITY_WORKFLOWS and sp.type_id != SupplyPointCodes.HSA:
            for year, month in months_between(BaseLevel.FACILITY_WAREHOUSE_START_DATE, sp.created_at):
                window_date = datetime(year, month, 1)

                for cls in warehouse_classes_with_product:
                    _init_with_product(cls, sp, window_date, BaseLevel.FACILITY)

                for cls in warehouse_classes_with_base_level:
                    _init_with_base_level(cls, sp, window_date, BaseLevel.FACILITY)

        SupplyPointWarehouseRecord.objects.create(supply_point=sp, create_date=datetime.utcnow())


def proper_children(supply_point):
    if supply_point.type_id == SupplyPointCodes.COUNTRY:
        # Skip over zone
        qs = SupplyPoint.objects.filter(active=True, supplied_by__supplied_by=supply_point)
    else:
        qs = SupplyPoint.objects.filter(active=True, supplied_by=supply_point)

    proper_child = proper_child_type(supply_point)
    if proper_child == 'hsa':
        # when the child type is HSAs also enforce that they should have an active
        # contact set to match hsa_supply_points_below
        qs = qs.filter(contact__is_active=True)
    if 'test' not in supply_point.name.lower():
        assert qs.count() == qs.filter(type__code=proper_child).count(), \
            '{0} ({1}) has the wrong number of children of the right type'.format(
                supply_point.name, supply_point.pk
            )
    return qs


def proper_child_type(supply_point):
    # For the purposes of the warehouse runner, do not collect aggregated data at the zone level
    return {
        'c': 'd',
        'd': 'hf',
        'hf': 'hsa',
        'hsa': None,
    }[supply_point.type.code]


def aggregate_types_in_order(base_level):
    if base_level == BaseLevel.HSA:
        yield SupplyPointCodes.FACILITY, 'health facility'
    yield SupplyPointCodes.DISTRICT, 'district'
    yield SupplyPointCodes.COUNTRY, 'country'


def _update_reporting_rate(supply_point, report_period, products_managed, base_level):
    """
    Process reports (on time versus late, versus at all and completeness)
    """
    late_cutoff = report_period.window_date + \
        timedelta(days=settings.LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT)

    # Filtering on base_level is not necessary for ProductReport because the supply_point
    # should tell what the base_level is (base_level will be HSA if the supply_point
    # is an hsa, and base_level will be FACILITY if the supply_point is a facility).
    # So since this is already a big query, it's better to not include the filter
    # for performance.
    reports_in_range = ProductReport.objects.filter(
        supply_point=supply_point,
        report_type__code=Reports.SOH,
        report_date__gte=report_period.period_start,
        report_date__lte=report_period.period_end,
    )
    period_rr = ReportingRate.objects.get_or_create(
        supply_point=supply_point,
        date=report_period.window_date,
        base_level=base_level,
    )[0]
    period_rr.total = 1
    period_rr.reported = 1 if reports_in_range else period_rr.reported
    if reports_in_range:
        first_report_date = reports_in_range.order_by('report_date')[0].report_date
        period_rr.on_time = first_report_date <= late_cutoff or period_rr.on_time

    if not period_rr.complete:
        # check for completeness (only if not already deemed complete)
        # unfortunately, we have to walk all avaialable
        # transactions in the period every month
        # in order to do this correctly.
        this_months_reports = ProductReport.objects.filter(
            supply_point=supply_point,
            report_type__code=Reports.SOH,
            report_date__gte=report_period.window_date,
            report_date__lte=report_period.period_end,
        )

        found = set(this_months_reports.values_list("product", flat=True).distinct())
        period_rr.complete = 0 if found and (products_managed - found) else \
            (1 if found else 0)

    period_rr.save()


def _update_product_availability(supply_point, report_period, all_products, products_managed, base_level):
    """
    Compute ProductAvailabilityData
    """
    # NOTE: this currently calculates everything on a
    # per-month basis. if it is determined that we only
    # need current information, the models can be cleaned
    # up a bit
    for p in all_products:
        product_data, created = ProductAvailabilityData.objects.get_or_create\
            (product=p, supply_point=supply_point,
             date=report_period.window_date)

        if created:
            # initally assume we have no data on anything
            product_data.without_data = 1

        transactions = StockTransaction.objects.filter(
            supply_point=supply_point, product=p,
            date__gte=report_period.period_start,
            date__lt=report_period.period_end).order_by('-date')
        product_data.total = 1
        product_data.managed = 1 if p.pk in products_managed else 0
        if transactions:
            trans = transactions[0]
            product_stock = ProductStock.objects.get(
                product=trans.product, supply_point=supply_point
            )

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
        (supply_point=supply_point,
         date=report_period.window_date,
         base_level=base_level)[0]
    product_summary.total = 1

    if products_managed:
        product_summary.any_managed = 1
        agg_results = ProductAvailabilityData.objects.filter(
            supply_point=supply_point,
            date=report_period.window_date,
            managed=1,
            product__type__base_level=base_level
        ).aggregate(
            *[Max("managed_and_%s" % c) for c in ProductAvailabilityData.STOCK_CATEGORIES]
        )
        for c in ProductAvailabilityData.STOCK_CATEGORIES:
            setattr(product_summary, "any_%s" % c,
                    agg_results["managed_and_%s__max" % c])
            assert getattr(product_summary, "any_%s" % c) <= 1
    else:
        product_summary.any_managed = 0
        for c in ProductAvailabilityData.STOCK_CATEGORIES:
            setattr(product_summary, "any_%s" % c, 0)

    product_summary.save()


def _update_lead_times(hsa, report_period):
    # ord-ready

    # NOTE: the existing code currently also removes
    # status 'canceled'. Is this necessary?
    requests_in_range = StockRequest.objects.filter(\
        responded_on__gte=report_period.period_start,
        responded_on__lt=report_period.period_end,
        supply_point=hsa
    ).exclude(requested_on=None)
    or_tt = TimeTracker.objects.get_or_create\
        (supply_point=hsa, date=report_period.window_date,
         type=TimeTrackerTypes.ORD_READY)[0]
    for r in requests_in_range:
        lt = delta_secs(r.responded_on - r.requested_on)
        or_tt.time_in_seconds += lt
        or_tt.total += 1
    or_tt.save()

    # ready-receieved
    requests_in_range = StockRequest.objects.filter(\
        received_on__gte=report_period.period_start,
        received_on__lt=report_period.period_end,
        supply_point=hsa
    ).exclude(responded_on=None)
    rr_tt = TimeTracker.objects.get_or_create\
        (supply_point=hsa, date=report_period.window_date,
         type=TimeTrackerTypes.READY_REC)[0]
    for r in requests_in_range:
        lt = delta_secs(r.received_on - r.responded_on)
        rr_tt.time_in_seconds += lt
        rr_tt.total += 1
    rr_tt.save()


def _update_order_requests(hsa, report_period, all_products):
    requests_in_range = StockRequest.objects.filter(\
        requested_on__gte=report_period.period_start,
        requested_on__lt=report_period.period_end,
        supply_point=hsa
    )
    for p in all_products:
        ord_req = OrderRequest.objects.get_or_create\
            (supply_point=hsa, date=report_period.window_date, product=p)[0]
        ord_req.total += requests_in_range.filter(product=p).count()
        ord_req.emergency += requests_in_range.filter(product=p, is_emergency=True).count()
        ord_req.save()


def _update_order_fulfillment(hsa, report_period, all_products):
    requests_in_range = StockRequest.objects.filter(
        received_on__gte=report_period.period_start,
        received_on__lt=report_period.period_end,
        supply_point=hsa,
    ).exclude(Q(amount_requested=None) | Q(amount_received=None))
    for p in all_products:
        order_fulfill = OrderFulfillment.objects.get_or_create\
            (supply_point=hsa, date=report_period.window_date, product=p)[0]
        for r in requests_in_range.filter(product=p):
            order_fulfill.total += 1
            order_fulfill.quantity_requested += r.amount_requested
            order_fulfill.quantity_received += r.amount_received
        if requests_in_range.count():
            order_fulfill.save()


def _update_historical_stock(supply_point, report_period, all_products):
    # set the historical stock values to the last report before
    # the end of the period (even if it's not in the period)
    for p in all_products:
        hs = HistoricalStock.objects.get_or_create\
            (supply_point=supply_point, date=report_period.window_date, product=p)[0]

        transactions = StockTransaction.objects.filter(
            supply_point=supply_point,
            product=p,
            date__lt=report_period.period_end,
        ).order_by('-date')

        hs.total = 1
        if transactions.count():
            hs.stock = transactions[0].ending_balance
        hs.save()
