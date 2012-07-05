import json
from datetime import datetime

from django.core.urlresolvers import reverse

from logistics.models import SupplyPoint, Product, StockTransaction, ProductStock
from logistics.reports import ProductAvailabilitySummaryByFacilitySP

from logistics_project.apps.tanzania.models import SupplyPointStatus
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.utils import submitted_to_msd

from logistics_project.apps.tanzania.reporting.models import *

TESTING = True

# initial population

# @task
def generate():
    running = ReportRun.objects.filter(complete=False)
    if len(running) > 0:
        return "Already running..."

    # start new run
    new_run = ReportRun(start_time=datetime.utcnow())
    create_object(new_run)

    start_date = datetime.fromordinal(datetime.utcnow().toordinal()-90) # make this configurable?
    last_run = ReportRun.objects.all().order_by('-start_time')
    if (last_run) > 0:
        start_date = last_run[0].start_time
    end_date = datetime.utcnow()

    populate_report_data(start_date, end_date)

    # complete run
    new_run.end_time = datetime.utcnow()
    new_run.complete = True
    create_object(new_run)

def cleanup():
    clean_up_since = datetime.fromordinal(datetime.utcnow().toordinal()-90)

    start_date = clean_up_since
    end_date = datetime.utcnow()

    clear_out_reports(start_date, end_date)
    populate_report_data(start_date, end_date)

def clear_out_reports(start_date, end_date):
    if TESTING:
        pass
    else:
        org_summary = OrganizationSummary.objects.filter(date__range=(start_date,end_date))
        group_summary = GroupSummary.objects.filter(org_summary__date__range=(start_date,end_date))
        group_data = GroupData.objects.filter(group_summary__org_summary__date__range=(start_date,end_date))
        product_availability = ProductAvailabilityData.objects.filter(date__range=(start_date,end_date))
        product_dashboard = ProductAvailabilityDashboardChart.objects.filter(date__range=(start_date,end_date))

        org_summary.delete()
        group_summary.delete()
        group_data.delete()
        product_availability.delete()
        product_dashboard.delete()
    
def populate_report_data(start_date, end_date):
    for org in SupplyPoint.objects.all(): # .order_by('name'):

        print org.name + ' (' + str(org.id) + ')'
        
        def get_children(sp, num_levels=4, child_orgs=[]):
            for s in SupplyPoint.objects.filter(supplied_by__id=sp):
                child_orgs.append(s.id)
                get_children(s.id,num_levels-1)
            return child_orgs

        child_orgs = get_children(org.id)
        child_orgs.append(org.id)

        new_trans = StockTransaction.objects.filter(supplypoint_id__in=child_orgs, date__gte=start_date)
        new_statuses = SupplyPointStatus.objects.filter(supplypoint_id__in=child_orgs, status_date__gte=start_date)

        process_statuses(org, new_statuses)
        process_trans(org, new_trans)

        # run_alerts(org, datetime(year,month,1), child_orgs)

        # for year in range(start_date.year,end_date.year + 1):
        #     for month in range(1 if year > start_date.year else start_date.month,13 if year < end_date.year else end_date.month%12 + 1):                
        #         populate_no_primary_alerts(org, datetime(year,month,1), child_orgs)                
        #         report_data = SupplyPointStatusBreakdown(SupplyPoint.objects.filter(id__in=child_orgs, type__code='facility', active=True),year=year,month=month)
        #         product_data = ProductAvailabilitySummaryByFacilitySP(SupplyPoint.objects.filter(id__in=child_orgs, type__code='facility', active=True),year=year,month=month)
        #         msd_data = submitted_to_msd(child_orgs, month, year)
        #         populate_group_data_plus_alerts(org, datetime(year,month,1), report_data, msd_data)
        #         populate_product_data(org,datetime(year,month,1),product_data)
        #         populate_stockout_alerts(org, datetime(year,month,1), child_orgs)

def process_statuses(org, statuses):
    for status in statuses:
        date = status.status_date
        status_type = status.status_type
        status_value = status.status_value
        sp = status.supply_point
        group_data.objects.filter(group_summary__org_summary__organization=sp.supplied_by)
        for gd in group_data:
            if gd.label==status_value: # almost
                gd.number += 1
                create_object(gd)
                # gs = gd.group_summary
                # gs.historical_response_rate
                # create_object(gs)

def process_trans(org, trans):
    for tran in trans:
        date = tran.date
        product_data = ProductAvailabilityData.objects.get_or_create(product=tran.product, organization=org, date=datetime(date.year, date.month, 1))
        if tran.ending_balance <= 0:
            product_data.without_stock += 1
        else:
            product_data.with_stock += 1
        product_data.total += 1
        # duplicates
        # without data
        create_object(product_data)

def populate_group_data_plus_alerts(org, date, data, msd_data):
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


def populate_product_data(org,date,data):
    
    for chart in json.loads(data.flot_data['data']):
        product_dashboard = ProductAvailabilityDashboardChart(organization=org, date=date,
                                                              width=data.width,
                                                              height=data.height,
                                                              div=data.div,
                                                              legenddiv=data.legenddiv,
                                                              xaxistitle=data.xaxistitle,
                                                              yaxistitle=data.yaxistitle)    
    
        product_dashboard.label = chart['label']
        product_dashboard.color = chart['color']
        create_object(product_dashboard)

    for product in data.data:
        product_availability = ProductAvailabilityData(organization=org, date=date)
        product_availability.product = product['product']
        product_availability.total = product['total']
        product_availability.with_stock = max(product['with_stock'],0)
        product_availability.without_stock = max(product['without_stock'],0)
        product_availability.without_data = max(product['without_data'],0)
        create_object(product_availability)

def populate_no_primary_alerts(org, date, child_orgs):
    no_primary = SupplyPoint.objects.filter(id__in=child_orgs, contact=None)
    for problem in no_primary:
        create_alert(org,date,'no_primary_contact',{'org': problem})

def populate_stockout_alerts(org, date, child_orgs):
    stockouts = ProductStock.objects.filter(supply_point__id__in=child_orgs, quantity=0)
    for problem in stockouts:
        create_alert(org,date,'product_stockout',{'org': problem.supply_point, 'product': problem.product})

def create_alert(org, date, type, details):
    alert = Alert(organization=org, date=date)
    alert.expires = datetime.fromordinal(date.toordinal()+32)
    alert.url = ''

    if type=='rr_not_submitted':
        alert.text = '%d facilities have reported not submitting their R&R form as of today.' % details['number']
    elif type=='rr_not_responded':
        alert.text = '%d facilities did not respond to the SMS asking if they had submitted their R&R form.' % details['number']
    elif type=='delivery_not_received':
        alert.text = '%d facilities have reported not receiving their deliveries as of today.' % details['number']
    elif type=='delivery_not_responding':
        alert.text = '%d facilities did not respond to the SMS asking if they had received their delivery.' % details['number']        
    elif type=='soh_not_responding':
        alert.text = '%d facilities have not reported their stock levels for last month.' % details['number']
        alert.url = reverse('facilities_index')
    elif type=='product_stockout':
        alert.text = '%s is stocked out of %s.' % (details['org'].name, details['product'].name)
    elif type=='no_primary_contact':
        alert.text = '%s has no primary contact.' % details['org'].name

    create_object(alert)

##########
# temporary for testing
##########
def create_object(obj):
    if TESTING:
        pass
    else:
        obj.save()


print datetime.now()
generate()
print datetime.now()