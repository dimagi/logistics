import json
from datetime import datetime

from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q

from logistics.models import SupplyPoint, Product, StockTransaction, ProductStock
from logistics.reports import ProductAvailabilitySummaryByFacilitySP

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

        new_statuses = SupplyPointStatus.objects.filter(supply_point__in=child_objs, status_date__gte=start_date).order_by('id')
        new_trans = StockTransaction.objects.filter(supply_point__in=child_objs, date__gte=start_date).order_by('id')

        statuses = process_statuses(org, new_statuses, child_objs)
        trans = process_trans(org, new_trans, child_objs)

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
                populate_stockout_alerts(org, datetime(year,month,1), child_objs)

                not_responding(org_summary, child_objs)

def not_responding(org_summary, child_objs):
    dg = DeliveryGroups(month=org_summary.date.month)
    submitting_group = dg.current_submitting_group()
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
        new_gd = GroupData.objects.get_or_create(group_summary=gsum, label='not_responding')[0]
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

def process_statuses(org, statuses, child_objs):
    processed = []
    def recent_reminder(sp, date, type):
        recent_statuses = SupplyPointStatus.objects.filter(supply_point=sp, status_type=type, 
                                            status_date__gte=datetime.fromordinal(date.toordinal()-5))
        for status in recent_statuses:
            if status.status_value == SupplyPointStatusValues.REMINDER_SENT:
                return True
        return False

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
        if group_data.complete:
            if recent_reminder(sp, status.status_date, status.status_type):
                group_data.on_time = True
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


print datetime.now()
cleanup()
generate()
print datetime.now()