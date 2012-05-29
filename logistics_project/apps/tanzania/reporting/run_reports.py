from datetime import datetime
import json

from logistics.models import SupplyPoint, Product, StockTransaction
from logistics.reports import ProductAvailabilitySummaryByFacilitySP

from logistics_project.apps.tanzania.models import SupplyPointStatus
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.reporting.models import *


# @task
def generate():
    # only clear/repopulate recent time period
    clear_out_reports()
    populate_report_data()

def clear_out_reports():
    ds = DistrictSummary.objects.all()
    pas = ProductAvailabilitySummary.objects.all()
    sp = SOHPie.objects.all()
    rp = RRPie.objects.all()
    svp = SupervisionPie.objects.all()
    dp = DeliveryPie.objects.all()
    pie_charts = PieCharts.objects.all()

    ds.delete()
    pas.delete()
    sp.delete()
    rp.delete()
    svp.delete()
    dp.delete()
    pie_charts.delete()
    
def populate_report_data():
    for org in SupplyPoint.objects.iterator():
        print org.name
        def get_children(sp, num_levels=4, child_orgs=[]):
            for s in SupplyPoint.objects.filter(supplied_by__id=sp):
                child_orgs.append(s.id)
                get_children(s.id,num_levels-1)
            return child_orgs

        child_orgs = get_children(org.id)

        for year in range(2012,datetime.now().year + 1):
            for month in range(1,13 if year < datetime.now().year else datetime.now().month%12 + 1):
                print datetime(year,month,1)
                report_data = SupplyPointStatusBreakdown(SupplyPoint.objects.filter(id__in=child_orgs, type__code='facility', active=True),year,month)
                product_data = ProductAvailabilitySummaryByFacilitySP(SupplyPoint.objects.filter(id__in=child_orgs, type__code='facility', active=True),year=year,month=month)
                populate_data(org, report_data)
                populate_product_data(org,datetime(year,month,1),product_data)

def populate_data(org, data):
    ds = DistrictSummary(organization = org)
    date = datetime(data.year,data.month,1)
    ds.date = date

    submit_group = data.dg.current_submitting_group()
    ds.submit_group = submit_group
    submit_facs = data.dg.submitting()
    submit_complete = data.submitted

    processing_group = data.dg.current_processing_group()
    ds.processing_group = processing_group
    processing_facs = data.dg.processing()
    processing_complete = []

    delivery_group = data.dg.current_delivering_group()
    ds.delivery_group = delivery_group
    delivery_facs = data.dg.delivering()
    delivery_complete = data.delivery_received

    total = data.dg.total().count()
 
    ds.total_facilities = total

    for i in ['submit','processing','delivery']:
        exec('ds.group_%s_total = %s_facs.count()' % (eval(i + '_group.lower()'), i))
        exec('ds.group_%s_complete = len(%s_complete)' % (eval(i + '_group.lower()'), i))

    ds.average_lead_time_in_days = data.avg_lead_time2

    create_object(ds)

    pie_charts = PieCharts(organization = org, date = date)
    pie_charts.soh_title = data.soh_chart().title
    pie_charts.soh_json = json.dumps(data.soh_chart().data)
    pie_charts.randr_title = data.submission_chart().title
    pie_charts.randr_json = json.dumps(data.submission_chart().data)
    pie_charts.supervision_title = data.supervision_chart().title
    pie_charts.supervision_json = json.dumps(data.supervision_chart().data)
    pie_charts.delivery_title = data.delivery_chart().title
    pie_charts.delivery_json = json.dumps(data.delivery_chart().data)

    create_object(pie_charts)

    sp = SOHPie(organization = org, date = date)
    sp.on_time = len(data.soh_on_time)
    sp.late = len(data.soh_late)
    sp.not_responding = len(data.soh_not_responding)
    
    create_object(sp)


    rp = RRPie(organization = org, date = date)
    rp.on_time = len(data.submitted_on_time)
    rp.late = len(data.submitted_late)
    rp.not_submitted = len(data.not_submitted)
    rp.not_responding = len(data.submit_not_responding)
    rp.historical_response_rate = data.randr_response_rate2()

    create_object(rp)


    svp = SupervisionPie(organization = org, date = date)
    svp.received = len(data.supervision_received)
    svp.not_received = len(data.supervision_not_received)
    svp.not_responding = len(data.supervision_not_responding)
    svp.historical_response_rate = data.supervision_response_rate2()

    create_object(svp)


    dp = DeliveryPie(organization = org, date = date)
    dp.received = len(data.delivery_received)
    dp.not_received = len(data.delivery_not_received)
    dp.not_responding = len(data.delivery_not_responding)
    dp.average_lead_time_in_days = data.avg_lead_time2

    create_object(dp)


def populate_product_data(org,date,data):
    
    pas = ProductAvailabilitySummary(organization = org, date = date)
    pas.data = data.data
    pas.width = data.width
    pas.height = data.height
    pas.div = data.div
    pas.legenddiv = data.legenddiv
    pas.flot_data = data.flot_data
    pas.xaxistitle = data.xaxistitle
    pas.yaxistitle = data.yaxistitle
    pas.max_value = data.max_value

    create_object(pas)


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