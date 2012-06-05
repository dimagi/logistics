import json
from datetime import datetime

from logistics.models import SupplyPoint, Product, StockTransaction
from logistics.reports import ProductAvailabilitySummaryByFacilitySP

from logistics_project.apps.tanzania.models import SupplyPointStatus
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.reporting.models import *


# @task
def generate():
    clear_since_date = datetime(datetime.utcnow().year-1, datetime.utcnow().month, 1)
    start_date = datetime.fromordinal(datetime.utcnow().toordinal()-90)
    end_date = datetime.utcnow()

    clear_out_reports(clear_since_date, end_date)
    populate_report_data(start_date, end_date)

def clear_out_reports(start_date, end_date):
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
    for org in SupplyPoint.objects.iterator():

        print org.name
        
        def get_children(sp, num_levels=4, child_orgs=[]):
            for s in SupplyPoint.objects.filter(supplied_by__id=sp):
                child_orgs.append(s.id)
                get_children(s.id,num_levels-1)
            return child_orgs

        child_orgs = get_children(org.id)

        for year in range(start_date.year,end_date.year + 1):
            for month in range(1 if year > start_date.year else start_date.month,13 if year < end_date.year else end_date.month%12 + 1):

                print datetime(year,month,1).strftime("%Y-%m")
                
                report_data = SupplyPointStatusBreakdown(SupplyPoint.objects.filter(id__in=child_orgs, type__code='facility', active=True),year,month)
                product_data = ProductAvailabilitySummaryByFacilitySP(SupplyPoint.objects.filter(id__in=child_orgs, type__code='facility', active=True),year=year,month=month)
                populate_group_data(org, datetime(year,month,1), report_data)
                populate_product_data(org,datetime(year,month,1),product_data)

def populate_group_data(org, date, data):
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
                    group_data.number = len(data.soh_not_responding)
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
                    group_data.number = len(data.not_submitted)
                elif fac_action == 'not_responding':
                    group_data.number = len(data.submit_not_responding)
                create_object(group_data)
        elif group_action == 'process':
            group_summary.historical_response_rate = data.supervision_response_rate2()
            create_object(group_summary)
            group_data = GroupData(group_summary=group_summary)
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
                    group_data.number = len(data.delivery_not_received)
                elif fac_action == 'not_responding':
                    group_data.number = len(data.delivery_not_responding)
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


##########
# temporary for testing
##########
def create_object(obj, testing=False):
    if testing:
        pass
    else:
        obj.save()


print datetime.now()
generate()
print datetime.now()