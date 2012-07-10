import json
from datetime import datetime

from django.core.urlresolvers import reverse

from logistics.models import SupplyPoint, Product, StockTransaction, ProductStock
from logistics.reports import ProductAvailabilitySummaryByFacilitySP

from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.utils import submitted_to_msd

from logistics_project.apps.tanzania.utils import calc_lead_time
from logistics_project.apps.tanzania.models import *
from logistics_project.apps.tanzania.reporting.models import *

TESTING = False
HISTORICAL_DAYS = 900
# log instead of print
# initial vs ongoing

# @task
def generate():
    running = ReportRun.objects.filter(complete=False)
    if len(running) > 0:
        print "Already running..."
        return

    # start new run
    new_run = ReportRun(start_time=datetime.utcnow())
    create_object(new_run)

    start_date = datetime.fromordinal(datetime.utcnow().toordinal() - HISTORICAL_DAYS)
    last_run = ReportRun.objects.all().order_by('-start_time')
    # if len(last_run) > 0:
    #     start_date = last_run[0].start_time
    end_date = datetime.utcnow()

    populate_report_data(start_date, end_date)

    # complete run
    new_run.end_time = datetime.utcnow()
    new_run.complete = True
    create_object(new_run)

def cleanup():
    clean_up_since = datetime.fromordinal(datetime.utcnow().toordinal() - HISTORICAL_DAYS)

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
    for org in SupplyPoint.objects.all().order_by('id'):

        print org.name + ' (' + str(org.id) + ')'
        
        def get_children(sp, num_levels=4, child_orgs=[]):
            for s in SupplyPoint.objects.filter(supplied_by__id=sp):
                child_orgs.append(s.id)
                get_children(s.id,num_levels-1)
            return child_orgs

        child_orgs = get_children(org.id)
        child_orgs.append(org.id)

        child_objs = SupplyPoint.objects.filter(id__in=child_orgs, active=True, type__code='facility')

        for year in range(start_date.year,end_date.year + 1):
            for month in range(1 if year > start_date.year else start_date.month,13 if year < end_date.year else end_date.month%12 + 1):
                org_summary = OrganizationSummary.objects.get_or_create(organization=org, date=datetime(year,month,1))[0]
                org_summary.total_orgs = len(child_objs)
                avg_lt = []
                for ch_org in child_objs:
                    lt = calc_lead_time(ch_org,year=year,month=month)
                    if lt: 
                        avg_lt.append(lt)
                org_summary.average_lead_time_in_days = sum(avg_lt)/len(avg_lt) if avg_lt else 0

                create_object(org_summary)
                populate_no_primary_alerts(org, datetime(year,month,1), child_objs)
                # other alerts go here
                populate_stockout_alerts(org, datetime(year,month,1), child_objs)

        new_statuses = SupplyPointStatus.objects.filter(supply_point__in=child_objs, status_date__gte=start_date)
        new_trans = StockTransaction.objects.filter(supply_point__in=child_objs, date__gte=start_date)

        statuses = process_statuses(org, new_statuses)
        trans = process_trans(org, new_trans)
        # no responses

def process_statuses(org, statuses):
    processed = []
    for status in statuses:
        sp = status.supply_point
        if sp.groups.all():
            sp_code = sp.groups.all()[0].code
        else:
            sp_code = ''
        org_summary = OrganizationSummary.objects.get_or_create(organization=org, date=datetime(status.status_date.year, status.status_date.month, 1))[0]
        group_summary = GroupSummary.objects.get_or_create(org_summary=org_summary, title=status.status_type)[0]
        group_summary.historical_responses += 1
        create_object(group_summary)
        group_data = GroupData.objects.get_or_create(group_summary=group_summary, group_code=sp_code, label=status.status_value)[0]
        group_data.number += 1
        group_data.complete = status.status_value in [SupplyPointStatusValues.SUBMITTED, SupplyPointStatusValues.RECEIVED]
        create_object(group_data)

        processed.append(group_data.id)
    return processed

def process_trans(org, trans):
    processed = []
    for tran in trans:
        date = tran.date
        product_data = ProductAvailabilityData.objects.get_or_create(product=tran.product, organization=org, date=datetime(date.year, date.month, 1))[0]
        if tran.ending_balance <= 0:
            product_data.without_stock += 1
        else:
            product_data.with_stock += 1
        product_data.total += 1
        create_object(product_data)

        processed.append(product_data.id)
    return processed

def populate_group_data_plus_alerts(org, date, data, msd_data):
    # alerts in here:
    #   soh not responding
    #   rr not submitted
    #   rr not responding
    #   delivery not received
    #   delivery not responding

    org_summary = OrganizationSummary(organization=org, date=date)
    org_summary.total_orgs = data.dg.total().count()
    org_summary.average_lead_time_in_days = data.avg_lead_time2

    create_object(org_summary)

    for group_action in ['soh_submit','rr_submit','process','deliver','supervision']:
        group_summary = GroupSummary(org_summary=org_summary)
        group_summary.title = group_action
        if group_action == 'soh_submit':
            create_object(group_summary)
            for fac_action in ['on_time','late','not_responding']:
                group_data = GroupData(group_summary=group_summary)
                group_data.label = fac_action
                if fac_action == 'on_time':
                    group_data.number = len(data.soh_on_time)
                    group_data.complete = True
                elif fac_action == 'late':
                    group_data.number = len(data.soh_late)
                    group_data.complete = True
                elif fac_action == 'not_responding':
                    temp = len(data.soh_not_responding)
                    group_data.number = temp
                    if temp > 0:
                        create_alert(org, date, 'soh_not_responding',{'number': temp})
                create_object(group_data)
        elif group_action == 'rr_submit':
            group_summary.historical_response_rate = data.randr_response_rate2()
            create_object(group_summary)
            for fac_action in ['on_time','late','not_submitted','not_responding']:
                group_data = GroupData(group_summary=group_summary)
                group_data.group_code = data.dg.current_submitting_group()
                group_data.label = fac_action
                if fac_action == 'on_time':
                    group_data.number = len(data.submitted_on_time)
                    group_data.complete = True
                elif fac_action == 'late':
                    group_data.number = len(data.submitted_late)
                    group_data.complete = True
                elif fac_action == 'not_submitted':
                    temp = len(data.not_submitted)
                    group_data.number = temp
                    if temp > 0:
                        create_alert(org, date, 'rr_not_submitted',{'number': temp})
                elif fac_action == 'not_responding':
                    temp = len(data.submit_not_responding)
                    group_data.number = temp
                    if temp > 0:
                        create_alert(org, date, 'rr_not_responded',{'number': temp})
                create_object(group_data)
        elif group_action == 'process':
            group_summary.historical_response_rate = data.supervision_response_rate2()
            create_object(group_summary)
            for status in ['complete', 'incomplete']:
                if status == 'complete':
                    group_data = GroupData(group_summary=group_summary)
                    group_data.complete = True
                    group_data.number = msd_data
                    group_data.group_code = data.dg.current_processing_group()
                    group_data.label = fac_action
                    create_object(group_data)
                elif status == 'incomplete':
                    group_data = GroupData(group_summary=group_summary)
                    group_data.complete = False
                    group_data.number = len(data.dg.processing()) - msd_data
                    group_data.group_code = data.dg.current_processing_group()
                    group_data.label = fac_action
                    create_object(group_data)                    
        elif group_action == 'deliver':
            group_summary.historical_response_rate = data.supervision_response_rate2()
            create_object(group_summary)
            for fac_action in ['received','not_received','not_responding']:
                group_data = GroupData(group_summary=group_summary)
                group_data.group_code = data.dg.current_delivering_group()
                group_data.label = fac_action
                if fac_action == 'received':
                    group_data.number = len(data.delivery_received)
                    group_data.complete = True
                elif fac_action == 'not_received':
                    temp = len(data.delivery_not_received)
                    group_data.number = temp
                    if temp > 0:
                        create_alert(org, date, 'delivery_not_received',{'number': temp})
                elif fac_action == 'not_responding':
                    temp = len(data.delivery_not_responding)
                    group_data.number = temp
                    if temp > 0:
                        create_alert(org, date, 'delivery_not_responding',{'number': temp})
                create_object(group_data)
        elif group_action == 'supervision':
            group_summary.historical_response_rate = data.supervision_response_rate2()
            create_object(group_summary)
            for fac_action in ['received','not_recieved','not_responding']:
                group_data = GroupData(group_summary=group_summary)
                group_data.label = fac_action
                if fac_action == 'received':
                    group_data.number = len(data.supervision_received)
                    group_data.complete = True
                elif fac_action == 'not_recieved':
                    group_data.number = len(data.supervision_not_received)
                elif fac_action == 'not_responding':
                    group_data.number = len(data.supervision_not_responding)
                create_object(group_data)

def populate_no_primary_alerts(org, date, child_objs):
    no_primary = child_objs.filter(contact=None).order_by('-name')
    for problem in no_primary:
        create_alert(org,date,'no_primary_contact',{'org': problem})

def populate_stockout_alerts(org, date, child_objs):
    stockouts = ProductStock.objects.filter(supply_point__in=child_objs, quantity=0)
    for problem in stockouts:
        create_alert(org,date,'product_stockout',{'org': problem.supply_point, 'product': problem.product})

def create_alert(org, date, type, details):
    text = ''
    url = ''
    expires = datetime.fromordinal(date.toordinal()+32)


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


print datetime.now()
cleanup()
generate()
print datetime.now()