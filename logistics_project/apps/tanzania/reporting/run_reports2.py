import json
from datetime import datetime

from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.db import transaction

from dimagi.utils.dates import months_between

from logistics.models import SupplyPoint, Product, StockTransaction, ProductStock
from logistics.reports import ProductAvailabilitySummaryByFacilitySP

from logistics_project.apps.tanzania.utils import calc_lead_time
from logistics_project.apps.tanzania.models import *
from logistics_project.apps.tanzania.reporting.models import *

TESTING = False
HISTORICAL_DAYS = 900

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
    ReportRun.objects.all().delete()
    running = ReportRun.objects.filter(complete=False)
    if len(running) > 0:
        print "Already running..."
        return

    start_date = start_date or datetime.fromordinal(datetime.utcnow().toordinal() - HISTORICAL_DAYS)
    # start new run
    now = datetime.utcnow()
    new_run = ReportRun(start_time=now)
    create_object(new_run)
    try: 
        last_run = ReportRun.objects.all().order_by('-start_time')
        # if len(last_run) > 0:
        #     start_date = last_run[0].start_time
        
        populate_report_data(start_date, now)
    
    finally:
        # complete run
        transaction.rollback()
        new_run.end_time = datetime.utcnow()
        new_run.complete = True
        create_object(new_run)

def cleanup(since=None):
    clean_up_since = since or datetime.fromordinal(datetime.utcnow().toordinal() - HISTORICAL_DAYS)

    start_date = clean_up_since
    end_date = datetime.utcnow()

    clear_out_reports(start_date, end_date)

def clear_out_reports(start_date, end_date):
    if TESTING:
        pass
    else:
        org_summary = OrganizationSummary.objects.filter(date__range=(start_date,end_date))
        group_summary = GroupSummary.objects.filter(org_summary__date__range=(start_date,end_date))
        group_data = GroupData.objects.filter(group_summary__org_summary__date__range=(start_date,end_date))
        product_availability = ProductAvailabilityData.objects.filter(date__range=(start_date,end_date))
        alerts = Alert.objects.filter(expires__range=(start_date,datetime.fromordinal(end_date.toordinal()+60)))

        org_summary.delete()
        group_summary.delete()
        group_data.delete()
        product_availability.delete()
        alerts.delete()
    
def populate_report_data(start_date, end_date):
    # first populate all the warehouse tables for all facilities
    facilities = SupplyPoint.objects.filter(active=True, type__code='facility').order_by('id')
    if True:
        for fac in facilities:
            print "processing facility %s (%s)" % (fac.name, str(fac.id))
            
            new_statuses = SupplyPointStatus.objects.filter\
                (supply_point=fac, status_date__gte=start_date,
                 status_date__lt=end_date).order_by('status_date')
            
            new_trans = StockTransaction.objects.filter\
                (supply_point=fac, date__gte=start_date, 
                 date__lt=end_date).order_by('date')
                 
            # process all the facility-level warehouse tables
            process_facility_statuses(fac, new_statuses)
            process_facility_transactions(fac, new_trans)
            
            # go through all the possible values in the date ranges
            # and make sure there are warehouse tables there 
            for year, month in months_between(start_date, end_date):
                window_date = datetime(year,month,1)
                org_summary, created = OrganizationSummary.objects.get_or_create\
                    (organization=fac, date=window_date)
                
                org_summary.total_orgs = 1
                alt = calc_lead_time(fac,year=year,month=month)
                if alt:
                    alt = alt.days
                org_summary.average_lead_time_in_days = alt or 0
                create_object(org_summary)
                
                # fill in the details:
                
                # TODO: alerts?
                # populate_no_primary_alerts(fac, window_date, [fac])
                # don't populate stockout alerts since they're broken
                # populate_stockout_alerts(fac, datetime(year,month,1), child_objs)
                
                # update all the non-response data
                not_responding_facility(org_summary)

    
    # then populate everything above a facility off a warehouse table
    non_facilities = SupplyPoint.objects.filter(active=True).exclude(type__code='facility').order_by('id')
    for org in non_facilities:
        
        def active_facilities_below(sp):
            for child in SupplyPoint.objects.filter(supplied_by=sp, active=True):
                for f in active_facilities_below(child):
                    yield f
            if sp.type.code == "facility":
                yield sp
            
        facs = list(active_facilities_below(org))
        print "processing non-facility %s (%s), %s children" % (org.name, str(org.id), len(facs))
        for year, month in months_between(start_date, end_date):
            window_date = datetime(year,month,1)
            org_summary = OrganizationSummary.objects.get_or_create\
                (organization=org, date=window_date)[0]
            
            org_summary.total_orgs = len(facs)
            sub_summaries = OrganizationSummary.objects.filter\
                (date=window_date, organization__in=facs)
        
            # lead times
            org_summary.average_lead_time_in_days = \
                sum([s.average_lead_time_in_days for s in sub_summaries]) / len(sub_summaries) \
                if sub_summaries else 0
            
            create_object(org_summary)    
            # product availability
            prods = Product.objects.all()
            for p in prods:
                product_data = ProductAvailabilityData.objects.get_or_create\
                    (product=p, organization=org, 
                     date=window_date)[0]
                
                sub_prods = ProductAvailabilityData.objects.filter\
                    (product=p, organization__in=facs, 
                     date=window_date)

                product_data.total = len(facs)
                product_data.with_stock = sum([p.with_stock for p in sub_prods])
                product_data.without_stock = sum([p.without_stock for p in sub_prods])
                product_data.without_data = product_data.total - product_data.with_stock \
                                                - product_data.without_stock
                create_object(product_data)
                
            
            for type in NEEDED_STATUS_TYPES:
                gsum = GroupSummary.objects.get_or_create\
                    (org_summary=org_summary, title=type)[0]
                sub_sums = GroupSummary.objects.filter\
                    (title=type, org_summary__in=sub_summaries).all()
                
                # TODO: see if moving the aggregation to the db makes it 
                # faster, if this is slow
                gsum.historical_responses = sum([s.historical_responses for s in sub_sums])
                gsum.no_responses = sum([s.no_responses for s in sub_sums])
                create_object(gsum)
                
                for response in SupplyPointStatusTypes.CHOICE_MAP[type].keys() + ['not_responding']:
                    gd = GroupData.objects.get_or_create\
                        (group_summary=gsum, label=response)[0]
                    sub_gds = GroupData.objects.filter\
                        (label=response, group_summary__in=sub_sums)
                    gd.number = sum([g.number for g in sub_gds])
                    gd.complete = sum([g.complete for g in sub_gds])
                    gd.on_time = sum([g.on_time for g in sub_gds])
                    create_object(gd)
                
                # TODO: above-facility-level alerts?
                # populate_no_primary_alerts(org, datetime(year,month,1), child_objs)
                # populate_stockout_alerts(org, datetime(year,month,1), child_objs)

        
def not_responding_facility(org_summary):
    assert org_summary.organization.type.code == "facility"
    
    dg = DeliveryGroups(month=org_summary.date.month)
    group = org_summary.organization.groups.all()[0].code 
    assert group, "Facility should belong to a group"    
    
    submitting_group = dg.current_submitting_group()
    delivery_group = dg.current_delivering_group()
    for type in NEEDED_STATUS_TYPES:
        gsum = GroupSummary.objects.get_or_create(org_summary=org_summary,
                                                  title=type)[0]
        new_gd = GroupData.objects.get_or_create(group_summary=gsum, 
                                                 label='not_responding')[0]
        
        assert gsum.historical_responses in (0, 1)
        if gsum.title == SupplyPointStatusTypes.SOH_FACILITY:
            new_gd.number = 1 - gsum.historical_responses
            if new_gd.number:
                # TODO: this might not be right unless we also clear it
                create_alert(org_summary.organization, org_summary.date, 
                             'soh_not_responding',{'number': new_gd.number})
        elif gsum.title == SupplyPointStatusTypes.SUPERVISION_FACILITY:
            new_gd.number = 1 - gsum.historical_responses
        elif gsum.title == SupplyPointStatusTypes.R_AND_R_FACILITY:
            new_gd.number = 1 - gsum.historical_responses if group == submitting_group else 0
            if new_gd.number:
                # TODO: this might not be right unless we also clear it
                create_alert(org_summary.organization, org_summary.date, 
                             'rr_not_responded',{'number': new_gd.number})        
        elif gsum.title == SupplyPointStatusTypes.DELIVERY_FACILITY:
            new_gd.number = 1 - gsum.historical_responses if group == delivery_group else 0
            if new_gd.number:
                # TODO: this might not be right unless we also clear it
                create_alert(org_summary.organization, org_summary.date, 
                             'delivery_not_responding',{'number': new_gd.number})
        else:
            # not an expected / needed group. ignore for now
            pass

        create_object(new_gd)


def recent_reminder(sp, date, type):
    """
    Return whether a reminder was sent in the 5 days immediately
    preceding the passed in date (with the right type and supply point)
    """
    return SupplyPointStatus.objects.filter\
        (supply_point=sp, status_type=type, 
         status_date__gt=datetime.fromordinal(date.toordinal()-5),
         status_date__lte=date,
         status_value=SupplyPointStatusValues.REMINDER_SENT).count() > 0
    

def process_facility_statuses(facility, statuses):
    """
    For a given facility and list of statuses, update the appropriate 
    data warehouse tables. This should only be called on supply points
    that are facilities.
    """
    assert facility.type.code == "facility"
    
    def _is_valid_status(facility, status):
        code = facility.groups.all()[0].code 
        dg = DeliveryGroups(status.status_date.month)
        if status.status_type.startswith('rr'):
            return code == dg.current_submitting_group()
        elif status.status_type.startswith('del'):
            return code == dg.current_delivering_group()
        return True
    
    for status in statuses:
        assert status.supply_point == facility
        if _is_valid_status(facility, status):
            sp_code = facility.groups.all()[0].code
            
            org_summary = OrganizationSummary.objects.get_or_create\
                (organization=facility, date=datetime(status.status_date.year, 
                                                      status.status_date.month, 1))[0]
            group_summary = GroupSummary.objects.get_or_create\
                (org_summary=org_summary, title=status.status_type)[0]
            
            if status.status_value not in (SupplyPointStatusValues.REMINDER_SENT,
                                          SupplyPointStatusValues.ALERT_SENT):
                # we've responded to this query
                group_summary.historical_responses = 1
            create_object(group_summary)
            
            group_data = GroupData.objects.get_or_create\
                (group_summary=group_summary, group_code=sp_code, 
                 label=status.status_value)[0]
            group_data.number = 1
            group_data.complete = 1 if status.status_value in [SupplyPointStatusValues.SUBMITTED, 
                                                               SupplyPointStatusValues.RECEIVED] \
                                    else 0 
            if group_data.complete:
                group_data.on_time = 1 if recent_reminder(facility, status.status_date, status.status_type)\
                                    else 0
        
            create_object(group_data)
            
            # update facility alerts
            if status.status_value==SupplyPointStatusValues.NOT_SUBMITTED \
                and status.status_type==SupplyPointStatusTypes.R_AND_R_FACILITY:
                create_alert(facility, status.status_date, 'rr_not_submitted',
                             {'number': group_data.number})
            
            if status.status_value==SupplyPointStatusValues.NOT_RECEIVED \
                and status.status_type==SupplyPointStatusTypes.DELIVERY_FACILITY:
                create_alert(facility, status.status_date, 'delivery_not_received',
                             {'number': group_data.number})
        
def process_facility_transactions(facility, transactions):
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
            (product=trans.product, organization=facility, 
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

def previously_without_data(transaction):
    trans = StockTransaction.objects.filter(product=transaction.product, supply_point=transaction.supply_point, 
                                            date__range=(transaction.date,datetime.fromordinal(datetime(transaction.date.year,transaction.date.month%12+1,1).toordinal()-1))).count()
    if trans > 1:
        return False
    return True

def populate_no_primary_alerts(org, date, child_objs):
    no_primary = child_objs.filter(contact=None).order_by('-name')
    for problem in no_primary:
        create_alert(org,date,'no_primary_contact',{'org': problem})

def populate_stockout_alerts(org, date, child_objs):
    raise NotImplementedError("this is broken and needs to be fixed!")
    stockouts = ProductStock.objects.filter(supply_point__in=child_objs, quantity=0)
    for problem in stockouts:
        create_alert(org,date,'product_stockout',{'org': problem.supply_point, 'product': problem.product})

def create_alert(org, date, type, details):
    text = ''
    url = ''
    expires = datetime(date.year, (date.month%12)+1, 1)

    if type=='rr_not_submitted':
        text = '%d facilities have reported not submitting their R&R form as of today.' % details['number']
    elif type=='rr_not_responded':
        text = '%d facilities did not respond to the SMS asking if they had submitted their R&R form.' % details['number']
    elif type=='delivery_not_received':
        text = '%d facilities have reported not receiving their deliveries as of today.' % details['number']
    elif type=='delivery_not_responding':
        text = '%d facilities did not respond to the SMS asking if they had received their delivery.' % details['number']        
    elif type=='soh_not_responding':
        text = '%d facilities have not reported their stock levels for last month.' % details['number']
        url = reverse('facilities_index')
    elif type=='product_stockout':
        text = '%s is stocked out of %s.' % (details['org'].name, details['product'].name)
    elif type=='no_primary_contact':
        text = '%s has no primary contact.' % details['org'].name

    alert = Alert.objects.get_or_create(organization=org, date=date, text=text, url=url, expires=expires)


##########
# temporary for testing
##########
def create_object(obj):
    if TESTING:
        pass
    else:
        obj.save()

# deprecated calls, temporarily left in for reference

def process_statuses(org, statuses, child_objs):
    processed = []
    
    for status in statuses:
        sp = status.supply_point
        if sp.groups.all():
            sp_code = sp.groups.all()[0].code
        else:
            sp_code = ''
        org_summary = OrganizationSummary.objects.get_or_create\
            (organization=org, date=datetime(status.status_date.year, 
                                             status.status_date.month, 1))[0]
        group_summary = GroupSummary.objects.get_or_create\
            (org_summary=org_summary, title=status.status_type)[0]
        
        group_summary.historical_responses += 1
        create_object(group_summary)
        group_data = GroupData.objects.get_or_create\
            (group_summary=group_summary, group_code=sp_code, 
             label=status.status_value)[0]
        group_data.number += 1
        group_data.complete = status.status_value in [SupplyPointStatusValues.SUBMITTED, SupplyPointStatusValues.RECEIVED]
        if group_data.complete:
            if recent_reminder(sp, status.status_date, status.status_type):
                group_data.on_time = True # NOTE: broken
        create_object(group_data)
        if status.status_value==SupplyPointStatusValues.NOT_SUBMITTED and status.status_type==SupplyPointStatusTypes.R_AND_R_FACILITY:
            create_alert(org, status.status_date, 'rr_not_submitted',{'number': group_data.number})
        if status.status_value==SupplyPointStatusValues.NOT_RECEIVED and status.status_type==SupplyPointStatusTypes.DELIVERY_FACILITY:
            create_alert(org, status.status_date, 'delivery_not_received',{'number': group_data.number})
        processed.append(group_data.id)
    return processed

def process_trans(org, trans, child_objs):
    processed = []
    for tran in trans:
        date = tran.date
        product_data = ProductAvailabilityData.objects.get_or_create(product=tran.product, organization=org, date=datetime(date.year, date.month, 1))
        subtract = product_data[1]
        data = product_data[0]
        if tran.ending_balance <= 0:
            data.without_stock += 1
            if not subtract and tran.beginning_balance > 0:
                data.with_stock = max(0, data.with_stock - 1)
        else:
            data.with_stock += 1
            if not subtract and tran.beginning_balance <=0:
                if previously_without_data(tran):
                    data.without_data = max(0, data.without_data - 1)
                else:                    
                    data.without_stock = max(0, data.without_stock - 1)
        data.total = len(child_objs)
        data.without_data = data.total - (data.with_stock + data.without_stock)
        create_object(data)

        processed.append(data.id)
    return processed


def not_responding(org_summary, child_objs):
    dg = DeliveryGroups(month=org_summary.date.month)
    submitting_group = dg.current_submitting_group()
    sp_code = org_summary.organization.groups.all()[0].code \
        if org_summary.organization.groups.count() else ''
    assert sp_code
    delivery_group = dg.current_delivering_group()
    submitting = child_objs.filter(groups__code=submitting_group)
    delivering = child_objs.filter(groups__code=delivery_group)
    group_summary = GroupSummary.objects.filter(org_summary=org_summary)
    for gsum in group_summary:
        total = 0
        group_data = GroupData.objects.exclude(Q(label=SupplyPointStatusValues.REMINDER_SENT)\
                                             | Q(label=SupplyPointStatusValues.ALERT_SENT)\
                                             | Q(label='not_responding')).filter(group_summary=gsum)
        for g in group_data:
            total += g.number
        new_gd = GroupData.objects.get_or_create(group_summary=gsum, 
                                                 label='not_responding', 
                                                 group_code=sp_code)[0]
        if gsum.title == SupplyPointStatusTypes.SOH_FACILITY:
            new_gd.number = len(child_objs) - total
            if new_gd.number:
                create_alert(org_summary.organization, org_summary.date, 'soh_not_responding',{'number': new_gd.number})
        if gsum.title == SupplyPointStatusTypes.SUPERVISION_FACILITY:
            new_gd.number = len(child_objs) - total
        if gsum.title == SupplyPointStatusTypes.R_AND_R_FACILITY:
            new_gd.number = len(submitting) - total
            if new_gd.number:
                create_alert(org_summary.organization, org_summary.date, 'rr_not_responded',{'number': new_gd.number})        
        if gsum.title == SupplyPointStatusTypes.DELIVERY_FACILITY:
            new_gd.number = len(delivering) - total
            if new_gd.number:
                create_alert(org_summary.organization, org_summary.date, 'delivery_not_responding',{'number': new_gd.number})


        create_object(new_gd)

