from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q

from dimagi.utils.dates import months_between, get_business_day_of_month, \
    add_months

from logistics.models import StockTransaction, ProductReport, Product

from logistics_project.apps.tanzania.models import SupplyPoint,\
    SupplyPointStatusTypes, SupplyPointStatus, SupplyPointStatusValues,\
    DeliveryGroups
from logistics_project.apps.tanzania.reporting.models import OrganizationSummary,\
    ProductAvailabilityData, GroupSummary, Alert
from logistics.const import Reports
from logistics.warehouse_models import SupplyPointWarehouseRecord
from django.core.exceptions import ObjectDoesNotExist

TESTING = False
HISTORICAL_DAYS = 900

# If default_to_previous is true then the system will use the previous values
# for product data, rather than making a new data point for each month.
PRODUCT_SUMMARY_DEFAULT_TO_PREVIOUS = True
    
# we enforce that all levels of the chain should have warehouse data 
# of each of these types
NEEDED_STATUS_TYPES = [SupplyPointStatusTypes.DELIVERY_FACILITY,
                       SupplyPointStatusTypes.R_AND_R_FACILITY,
                       SupplyPointStatusTypes.SUPERVISION_FACILITY,
                       SupplyPointStatusTypes.SOH_FACILITY]

# log instead of print
# initial vs ongoing

# @task
def generate(start_date=None):
    raise NotImplementedError("this method is removed and replaced with the warehouse command")
    
def cleanup(since=None):
    raise NotImplementedError("this method is removed and replaced with the warehouse command")
    
def clear_out_reports(start_date, end_date):
    if TESTING:
        pass
    else:
        org_summary = OrganizationSummary.objects.filter(date__range=(start_date, end_date))
        group_summary = GroupSummary.objects.filter(org_summary__date__range=(start_date, end_date))
        product_availability = ProductAvailabilityData.objects.filter(date__range=(start_date, end_date))
        alerts = Alert.objects.filter(expires__range=(start_date, datetime.fromordinal(end_date.toordinal() + 60)))

        org_summary.delete()
        group_summary.delete()
        product_availability.delete()
        alerts.delete()


def default_start_date():
    return datetime(2010, 11, 1)


def populate_report_data(start_date, end_date):
    # first populate all the warehouse tables for all facilities
    # hard coded to know this is the first date with data
    start_date = max(start_date, default_start_date())
    facilities = SupplyPoint.objects.filter(active=True, type__code='facility').order_by('id')
    for fac in facilities:
        process_facility_warehouse_data(fac, start_date, end_date)

    # then populate everything above a facility off a warehouse table
    non_facilities = SupplyPoint.objects.filter(active=True).exclude(type__code='facility').order_by('id')
    for org in non_facilities:
        process_non_facility_warehouse_data(org, start_date, end_date)

    # finally go back through the history and initialize empty data for any
    # newly created facilities
    update_historical_data()


def process_facility_warehouse_data(fac, start_date, end_date):
    """
    process all the facility-level warehouse tables
    """
    print "processing facility %s (%s)" % (fac.name, str(fac.id))


    for alert_type in ['soh_not_responding', 'rr_not_responded', 'delivery_not_responding']:
        alert = Alert.objects.filter(supply_point=fac, date__gte=start_date, date__lt=end_date, type=alert_type)
        alert.delete()

    new_statuses = SupplyPointStatus.objects.filter(
        supply_point=fac,
        status_date__gte=start_date,
        status_date__lt=end_date
    ).order_by('status_date')
    process_facility_statuses(fac, new_statuses)

    new_reports = ProductReport.objects.filter(
        supply_point=fac,
        report_date__gte=start_date,
        report_date__lt=end_date,
        report_type__code=Reports.SOH
    ).order_by('report_date')
    process_facility_product_reports(fac, new_reports)

    new_trans = StockTransaction.objects.filter(
        supply_point=fac,
        date__gte=start_date,
        date__lt=end_date
    ).order_by('date')
    process_facility_transactions(fac, new_trans)

    # go through all the possible values in the date ranges
    # and make sure there are warehouse tables there
    for year, month in months_between(start_date, end_date):
        window_date = datetime(year, month, 1)

        # create org_summary for every fac/date combo
        org_summary, created = OrganizationSummary.objects.get_or_create\
            (supply_point=fac, date=window_date)

        org_summary.total_orgs = 1
        alt = average_lead_time(fac, window_date)
        if alt:
            alt = alt.days
        org_summary.average_lead_time_in_days = alt or 0
        create_object(org_summary)

        # create group_summary for every org_summary title combo
        for title in NEEDED_STATUS_TYPES:
            group_summary, created = GroupSummary.objects.get_or_create(org_summary=org_summary,
                                                                        title=title)
        # update all the non-response data
        not_responding_facility(org_summary)

        # update product availability data
        update_product_availability_facility_data(org_summary)

        # alerts
        populate_no_primary_alerts(fac, window_date)
        populate_facility_stockout_alerts(fac, window_date)


def process_non_facility_warehouse_data(org, start_date, end_date):
    facs = list(active_facilities_below(org))
    print "processing non-facility %s (%s), %s children" % (org.name, str(org.id), len(facs))
    for year, month in months_between(start_date, end_date):
        window_date = datetime(year, month, 1)
        org_summary = OrganizationSummary.objects.get_or_create\
            (supply_point=org, date=window_date)[0]


        org_summary.total_orgs = len(facs)
        sub_summaries = OrganizationSummary.objects.filter\
            (date=window_date, supply_point__in=facs)

        subs_with_lead_time = [s for s in sub_summaries if s.average_lead_time_in_days]
        # lead times
        org_summary.average_lead_time_in_days = \
            sum([s.average_lead_time_in_days for s in subs_with_lead_time]) / len(subs_with_lead_time) \
            if subs_with_lead_time else 0

        create_object(org_summary)
        # product availability
        prods = Product.objects.all()
        for p in prods:
            product_data = ProductAvailabilityData.objects.get_or_create\
                (product=p, supply_point=org,
                 date=window_date)[0]

            sub_prods = ProductAvailabilityData.objects.filter\
                (product=p, supply_point__in=facs,
                 date=window_date)


            product_data.total = sum([p.total for p in sub_prods])
            assert product_data.total == len(facs), \
                "total should match number of sub facilities"
            product_data.with_stock = sum([p.with_stock for p in sub_prods])
            product_data.without_stock = sum([p.without_stock for p in sub_prods])
            product_data.without_data = product_data.total - product_data.with_stock \
                                            - product_data.without_stock
            create_object(product_data)


        dg = DeliveryGroups(month=month, facs=SupplyPoint.objects.filter(pk__in=[f.pk for f in facs]))
        for type in NEEDED_STATUS_TYPES:
            gsum = GroupSummary.objects.get_or_create\
                (org_summary=org_summary, title=type)[0]
            sub_sums = GroupSummary.objects.filter\
                (title=type, org_summary__in=sub_summaries).all()

            # TODO: see if moving the aggregation to the db makes it
            # faster, if this is slow
            gsum.total = sum([s.total for s in sub_sums])
            gsum.responded = sum([s.responded for s in sub_sums])
            gsum.on_time = sum([s.on_time for s in sub_sums])
            gsum.complete = sum([s.complete for s in sub_sums])
            # gsum.missed_response = sum([s.missed_response for s in sub_sums])
            create_object(gsum)

            if type == SupplyPointStatusTypes.DELIVERY_FACILITY:
                expected = dg.delivering().count()
            elif type == SupplyPointStatusTypes.R_AND_R_FACILITY:
                expected = dg.submitting().count()
            elif type == SupplyPointStatusTypes.SOH_FACILITY or \
                 type == SupplyPointStatusTypes.SUPERVISION_FACILITY:
                expected = len(facs)
            if gsum.total != expected:
                print "expected %s but was %s for %s" % (expected, gsum.total, gsum)

        for alert_type in ['rr_not_submitted', 'delivery_not_received',
                           'soh_not_responding', 'rr_not_responded', 'delivery_not_responding']:
            sub_alerts = Alert.objects.filter(supply_point__in=facs, date=window_date, type=alert_type)
            aggregate_response_alerts(org, window_date, sub_alerts, alert_type)


def not_responding_facility(org_summary):
    assert org_summary.supply_point.type.code == "facility"
    def needed_status_types(org_summary):
        return [type for type in NEEDED_STATUS_TYPES if \
                _is_valid_status(org_summary.supply_point, org_summary.date, type)]
    
    for type in needed_status_types(org_summary):
        gsum, created = GroupSummary.objects.get_or_create(org_summary=org_summary,
                                                  title=type)

        gsum.total = 1
        assert gsum.responded in (0, 1)
        if gsum.title == SupplyPointStatusTypes.SOH_FACILITY and not gsum.responded:
            # TODO: this might not be right unless we also clear it
            create_alert(org_summary.supply_point, org_summary.date,
                         'soh_not_responding', {'number': 1})
        elif gsum.title == SupplyPointStatusTypes.R_AND_R_FACILITY and not gsum.responded:
            # TODO: this might not be right unless we also clear it
            create_alert(org_summary.supply_point, org_summary.date,
                         'rr_not_responded', {'number': 1})        
        elif gsum.title == SupplyPointStatusTypes.DELIVERY_FACILITY and not gsum.responded:
            # TODO: this might not be right unless we also clear it
            create_alert(org_summary.supply_point, org_summary.date,
                         'delivery_not_responding', {'number': 1})
        else:
            # not an expected / needed group. ignore for now
            pass

        create_object(gsum)

def average_lead_time(fac, window_date):
    end_date = datetime(window_date.year, window_date.month % 12 + 1, 1)
    received = SupplyPointStatus.objects.filter(supply_point=fac,
                            status_date__lt=end_date,
                            status_value=SupplyPointStatusValues.RECEIVED,
                            status_type=SupplyPointStatusTypes.DELIVERY_FACILITY)\
                            .order_by('status_date')

    total_time = timedelta(days=0)
    count = 0

    last_receipt = datetime(1900, 1, 1)
    for receipt in received:
        if receipt.status_date - last_receipt < timedelta(days=30):
            last_receipt = receipt.status_date
            continue
        last_receipt = receipt.status_date
        last_submitted = SupplyPointStatus.objects.filter(supply_point=fac,
                            status_date__lt=receipt.status_date,
                            status_value=SupplyPointStatusValues.SUBMITTED,
                            status_type=SupplyPointStatusTypes.R_AND_R_FACILITY)\
                            .order_by('-status_date')
        if last_submitted.count():
            ltime = receipt.status_date - last_submitted[0].status_date
            if ltime > timedelta(days=30) and ltime < timedelta(days=100):
                total_time += ltime
                count += 1
        else:
            continue

    return total_time / count if count else None

def recent_reminder(sp, date, type):
    """
    Return whether a reminder was sent in the 5 days immediately
    preceding the passed in date (with the right type and supply point)
    """
    return SupplyPointStatus.objects.filter\
        (supply_point=sp, status_type=type,
         status_date__gt=datetime.fromordinal(date.toordinal() - 5),
         status_date__lte=date,
         status_value=SupplyPointStatusValues.REMINDER_SENT).count() > 0

def is_on_time(sp, status_date, warehouse_date, type):
    """
    on_time requirement    
    """
    if type == SupplyPointStatusTypes.SOH_FACILITY:
        if status_date.date() < get_business_day_of_month(warehouse_date.year, warehouse_date.month, 6):
            return True
    if type == SupplyPointStatusTypes.R_AND_R_FACILITY:
        if status_date.date() < get_business_day_of_month(warehouse_date.year, warehouse_date.month, 13):
            return True
    return False

def _is_valid_status(facility, date, type):
    if type not in NEEDED_STATUS_TYPES:
        return False

    if not facility.groups.count():
        return False

    code = facility.groups.all()[0].code
    dg = DeliveryGroups(date.month)
    if type.startswith('rr'):
        return code == dg.current_submitting_group()
    elif type.startswith('del'):
        return code == dg.current_delivering_group()
    return True

def _get_window_date(type, date):
    # we need this method because the soh and super reports actually
    # are sometimes treated as reports for _next_ month
    if type == SupplyPointStatusTypes.SOH_FACILITY or\
            type == SupplyPointStatusTypes.SUPERVISION_FACILITY:
        # if the date is after the last business day of the month
        # count it for the next month
        if date.date() >= get_business_day_of_month(date.year, date.month, -1):
            year, month = add_months(date.year, date.month, 1)
            return datetime(year, month, 1)
    return datetime(date.year, date.month, 1)

def process_facility_statuses(facility, statuses, alerts=True):
    """
    For a given facility and list of statuses, update the appropriate 
    data warehouse tables. This should only be called on supply points
    that are facilities.
    """
    assert facility.type.code == "facility"
    
    for status in statuses:
        assert status.supply_point == facility
        warehouse_date = _get_window_date(status.status_type, status.status_date)
        if _is_valid_status(facility, status.status_date, status.status_type):
            
            org_summary = OrganizationSummary.objects.get_or_create\
                (supply_point=facility, date=warehouse_date)[0]
            group_summary = GroupSummary.objects.get_or_create\
                (org_summary=org_summary, title=status.status_type)[0]
            
            group_summary.total = 1
            if status.status_value not in (SupplyPointStatusValues.REMINDER_SENT,
                                           SupplyPointStatusValues.ALERT_SENT):
                # we've responded to this query
                group_summary.responded = 1
            
            group_summary.complete = 1 if status.status_value in [SupplyPointStatusValues.SUBMITTED,
                                                                  SupplyPointStatusValues.RECEIVED] \
                                    else (group_summary.complete or 0)
            if group_summary.complete:
                group_summary.on_time = 1 if is_on_time(facility, status.status_date, warehouse_date, status.status_type)\
                                        else group_summary.on_time # if we already had an on-time, don't override a second one with late
            else:
                group_summary.on_time = 0
            
            create_object(group_summary)
            
            if alerts:
                # update facility alerts
                if status.status_value == SupplyPointStatusValues.NOT_SUBMITTED \
                    and status.status_type == SupplyPointStatusTypes.R_AND_R_FACILITY:
                    create_alert(facility, status.status_date, 'rr_not_submitted',
                                 {'number': 1})

                if status.status_value == SupplyPointStatusValues.NOT_RECEIVED \
                    and status.status_type == SupplyPointStatusTypes.DELIVERY_FACILITY:
                    create_alert(facility, status.status_date, 'delivery_not_received',
                                 {'number': 1})
            
def process_facility_product_reports(facility, reports):
    """
    For a given facility and list of ProductReports, update the appropriate 
    data warehouse tables. This should only be called on supply points
    that are facilities. Currently this only affects stock on hand reporting
    data. We need to use this method instead of the statuses because partial
    stock on hand reports don't create valid status, but should be treated
    like valid submissions in most of the rest of the site.
    """
    assert facility.type.code == "facility"
    months_updated = {}
    for report in reports:
        assert report.supply_point == facility
        assert report.report_type.code == Reports.SOH
        warehouse_date = _get_window_date(SupplyPointStatusTypes.SOH_FACILITY, report.report_date)
        
        if warehouse_date in months_updated:
            # an optimization to avoid repeatedly doing this work for each
            # product report for the entire month
            continue
        
        org_summary = OrganizationSummary.objects.get_or_create\
            (supply_point=facility, date=warehouse_date)[0]
        
        group_summary = GroupSummary.objects.get_or_create\
            (org_summary=org_summary, title=SupplyPointStatusTypes.SOH_FACILITY)[0]
        
        group_summary.total = 1
        group_summary.responded = 1
        group_summary.complete = 1 
        group_summary.on_time = 1 if is_on_time(facility, report.report_date, warehouse_date,
                                                SupplyPointStatusTypes.SOH_FACILITY)\
                                  else group_summary.on_time # if we already had an on-time, don't override a second one with late
        create_object(group_summary)
        months_updated[warehouse_date] = None # update the cache of stuff we've dealt with

def process_facility_transactions(facility, transactions, default_to_previous=True):
    """
    For a given facility and list of transactions, update the appropriate 
    data warehouse tables. This should only be called on supply points
    that are facilities.
    
    """
    assert facility.type.code == "facility"
    
    for trans in transactions:
        assert trans.supply_point == facility
        date = trans.date
        product_data = ProductAvailabilityData.objects.get_or_create\
            (product=trans.product, supply_point=facility,
             date=datetime(date.year, date.month, 1))[0]
        
        product_data.total = 1    
        product_data.without_data = 0
        if trans.ending_balance <= 0:
            product_data.without_stock = 1
            product_data.with_stock = 0
        else:
            product_data.without_stock = 0
            product_data.with_stock = 1
            
        create_object(product_data)

def update_product_availability_facility_data(org_summary):
    # product availability
    
    assert org_summary.supply_point.type.code == "facility"
    prods = Product.objects.all()
    for p in prods:
        product_data, created = ProductAvailabilityData.objects.get_or_create\
            (product=p, supply_point=org_summary.supply_point,
             date=org_summary.date)
        
        if created:
            # set defaults
            product_data.total = 1
            previous_reports = ProductAvailabilityData.objects.filter\
                (product=p, supply_point=org_summary.supply_point,
                 date__lt=org_summary.date)
            if PRODUCT_SUMMARY_DEFAULT_TO_PREVIOUS and previous_reports.count():
                prev = previous_reports.order_by("-date")[0]
                product_data.with_stock = prev.with_stock
                product_data.without_stock = prev.without_stock
                product_data.without_data = prev.without_data
            # otherwise we use the defaults
            else:
                product_data.with_stock = 0
                product_data.without_stock = 0
                product_data.without_data = 1
            create_object(product_data)
        assert (product_data.with_stock + product_data.without_stock \
                + product_data.without_data) == 1, "bad product data config"

def aggregate_response_alerts(org, date, alerts, type):
    total = sum([s.number for s in alerts])
    if total > 0:
        create_alert(org, date, type, {'number': total})

def populate_no_primary_alerts(org, date):
    # delete no primary alerts
    alert = Alert.objects.filter(supply_point=org, date=date, type='no_primary_contact')
    alert.delete()
    # create no primary alerts
    if not org.contacts():
        create_multilevel_alert(org, date, 'no_primary_contact', {'org': org})

def populate_facility_stockout_alerts(org, date):
    # delete stockout alerts
    alert = Alert.objects.filter(supply_point=org, date=date, type='product_stockout')
    alert.delete()
    # create stockout alerts
    product_data = ProductAvailabilityData.objects.filter(supply_point=org, date=date, without_stock=1)
    for p in product_data:
        create_multilevel_alert(org, date, 'product_stockout', {'org': org, 'product': p.product})

def create_multilevel_alert(org, date, type, details):
    create_alert(org, date, type, details)
    if org.supplied_by is not None:
        create_multilevel_alert(org.supplied_by, date, type, details)        

def create_alert(org, date, type, details):
    text = ''
    url = ''
    date = datetime(date.year, date.month, 1)
    expyear, expmonth = add_months(date.year, date.month, 1)
    expires = datetime(expyear, expmonth, 1)

    number = 0 if not details.has_key('number') else details['number']

    if type in ['product_stockout', 'no_primary_contact']:
        if type == 'product_stockout':
            text = '%s is stocked out of %s.' % (details['org'].name, details['product'].name)
        elif type == 'no_primary_contact':
            text = '%s has no primary contact.' % details['org'].name

        alert = Alert.objects.filter(supply_point=org, date=date, type=type, text=text)
        if not alert:
            create_object(Alert(supply_point=org, date=date, type=type, expires=expires, text=text))

    else:
        if type == 'rr_not_submitted':
            text = '%s have reported not submitting their R&R form as of today.' % \
                        ((str(number) + ' facility') if number == 1 else (str(number) + ' facilities'))
        elif type == 'rr_not_responded':
            text = '%s did not respond to the SMS asking if they had submitted their R&R form.' % \
                        ((str(number) + ' facility') if number == 1 else (str(number) + ' facilities'))
        elif type == 'delivery_not_received':
            text = '%s have reported not receiving their deliveries as of today.' % \
                        ((str(number) + ' facility') if number == 1 else (str(number) + ' facilities'))
        elif type == 'delivery_not_responding':
            text = '%s did not respond to the SMS asking if they had received their delivery.' % \
                        ((str(number) + ' facility') if number == 1 else (str(number) + ' facilities'))
        elif type == 'soh_not_responding':
            text = '%s have not reported their stock levels for last month.' % \
                        ((str(number) + ' facility') if number == 1 else (str(number) + ' facilities'))
            url = reverse('facilities_index')
    
        alert, created = Alert.objects.get_or_create(supply_point=org, date=date, type=type, expires=expires)
        alert.number = number
        alert.text = text
        alert.url = url
        create_object(alert)

def update_historical_data():
    """
    If we don't have a record of this supply point being updated, run
    through all historical data and just fill in with zeros.
    """
    start_date = OrganizationSummary.objects.order_by('date')[0].date
    for sp in SupplyPoint.objects.all():
        try:
            SupplyPointWarehouseRecord.objects.get(supply_point=sp)
        except ObjectDoesNotExist:
            # we didn't have a record so go through and historically update
            # anything we maybe haven't touched
            for year, month in months_between(start_date, sp.created_at):
                window_date = datetime(year, month, 1)
                for cls in [OrganizationSummary, ProductAvailabilityData, GroupSummary]:
                    _init_warehouse_model(cls, sp, window_date)
            SupplyPointWarehouseRecord.objects.create(supply_point=sp,
                                                      create_date=datetime.utcnow())

def _init_warehouse_model(cls, supply_point, date):
    {
        OrganizationSummary: _init_default,
        ProductAvailabilityData: _init_with_product,
        GroupSummary: _init_group_summary
    }[cls](cls, supply_point, date)

def _init_default(cls, supply_point, date):
    cls.objects.get_or_create(supply_point=supply_point, date=date)

def _init_with_product(cls, supply_point, date):
    for p in Product.objects.all():
        cls.objects.get_or_create(supply_point=supply_point, date=date, product=p)

def _init_group_summary(cls, supply_point, date):
    assert cls == GroupSummary
    org_summary = OrganizationSummary.objects.get(supply_point=supply_point, date=date)
    for title in NEEDED_STATUS_TYPES:
        GroupSummary.objects.get_or_create(org_summary=org_summary,
                                           title=title)


##########
# temporary for testing
##########
def create_object(obj):
    if TESTING:
        pass
    else:
        obj.save()

def active_facilities_below(sp):
    for child in SupplyPoint.objects.filter(supplied_by=sp):
        for f in active_facilities_below(child):
            yield f
    if sp.type.code == "facility" and sp.active:
        yield sp
