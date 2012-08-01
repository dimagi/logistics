'''
New views for the upgraded reports of the system.
'''
from random import random
from datetime import datetime, timedelta
from collections import defaultdict

from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.utils.datastructures import SortedDict

from dimagi.utils.decorators.datespan import datespan_in_request
from dimagi.utils.dates import months_between, DateSpan, add_months


from logistics.models import Product, SupplyPoint
from logistics.decorators import place_in_request

from logistics_project.apps.malawi.util import get_facilities, get_districts,\
    get_country_sp, get_district_supply_points, facility_supply_points_below,\
    pct, fmt_pct
from logistics.util import config
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData,\
    ProductAvailabilityDataSummary, ReportingRate, OrderRequest
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart,\
    current_report_period

REPORT_LIST = SortedDict([
    ("Dashboard", "dashboard"),
    ("Reporting Rate", "reporting-rate"),
    ("Stock Status", "stock-status"),
    ("Consumption Profiles", "consumption-profiles"),
    ("Alert Summary", "alert-summary"),
    ("Re-supply Qts Required", "re-supply-qts-required"),
    ("Lead Times", "lead-times"),
    ("Order Fill Rate", "order-fill-rate"),
    ("Emergency Orders", "emergency-orders"),
])

to_stub = lambda x: {"name": x, "slug": REPORT_LIST[x]}

stub_reports = [to_stub(r) for r in REPORT_LIST.keys()]

def malawi_default_date_func():
    # we default to showing the last three months
    now = datetime.utcnow()
    startyear, startmonth = add_months(now.year, now.month, -2)
    return DateSpan(datetime(startyear, startmonth, 1),
                    datetime(now.year, now.month, 1),
                    format='%B %Y')
     
datespan_default = datespan_in_request(
    default_function=malawi_default_date_func,
    format_string='%B %Y'
)

def home(request):
    return redirect("/malawi/r/dashboard/")
    
@place_in_request()
@datespan_default
def get_report(request, slug=''):
    context = shared_context(request)
    context.update({"report_list": stub_reports,
                    "slug": slug})
    
    context.update(get_more_context(request, slug))
    return render_to_response("malawi/new/%s.html" % slug, 
                              context,
                              context_instance=RequestContext(request))


def get_more_context(request, slug=None):
    func_map = {
        'dashboard': dashboard_context,
        'emergency-orders': eo_context,
        'order-fill-rate': ofr_context,
        're-supply-qts-required': rsqr_context,
        'alert-summary': as_context,
        'consumption-profiles': cp_context,
        'stock-status': ss_context,
        'lead-times': lt_context,
        'reporting-rate': rr_context,
    }
    if slug in func_map:
        return func_map[slug](request)
    else:
        return {}

    context = func_map[slug](request) if slug in func_map else {}
    context["slug"] = slug
    return context 

def shared_context(request):
    products = Product.objects.all().order_by('sms_code')
    country = get_country_sp()
    date = current_report_period()
    
    # national stockout percentages by product
    stockout_pcts = SortedDict()
    for p in products:
        availability = ProductAvailabilityData.objects.get(supply_point=country,
                                                           date=date,
                                                           product=p)
        stockout_pcts[p] = pct(availability.managed_and_without_stock,
                               availability.managed)
    
    
    current_rr = ReportingRate.objects.get\
        (date=date, supply_point=country)
    return { 
        "settings": settings,
        "report_list": stub_reports,
        "location": request.location or country.location,
        "districts": get_districts(),
        "facilities": get_facilities(),
        "hsas": SupplyPoint.objects.filter(active=True, type__code="hsa").count(),
        "reporting_rate": current_rr.pct_reported,
        "products": products,
        "product_stockout_pcts": stockout_pcts,
    }

def timechart(labels):
    summary = {
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        # "width": "730px",
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "month",
        "yaxistitle": "rate"
    }
    summary['xlabels'] = _month_labels(datetime.now() - timedelta(days=61), datetime.now())
    summary['data'] = barseries(labels, len(summary['xlabels']))
    return summary


def barseries(labels, num_points):
    return [{"label": l, "data": bardata(num_points)} for l in labels]
    
def bardata(num_points):
    return [[i + 1, random()] for i in range(num_points)]

def _month_labels(start_date, end_date):
    return [[i + 1, '<span>%s</span>' % datetime(year, month, 1).strftime("%b")] \
            for i, (year, month) in enumerate(months_between(start_date, end_date))]
    
def dashboard_context(request):
    window_date = _get_window_date(request)

    # reporting rates + stockout summary
    districts = get_districts().order_by('name')
    summary_data = SortedDict()
    for d in districts:
        avail_sum = ProductAvailabilityDataSummary.objects.get(supply_point=d, date=window_date)
        stockout_pct = pct(avail_sum.with_any_stockout,
                             avail_sum.manages_anything) 
        rr = ReportingRate.objects.get(supply_point=d, date=window_date)
        reporting_rate = pct(rr.reported, rr.total)
        summary_data[d] = {"stockout_pct": stockout_pct,
                           "reporting_rate": reporting_rate}
    
    # report chart
    return {"summary_data": summary_data,
            "graphdata": get_reporting_rates_chart(request.location, 
                                                   request.datespan.startdate, 
                                                   window_date),
            "pa_width": 530 if settings.STYLE=='both' else 730 }

def eo_context(request):
    sp_code = request.GET.get('place') or get_country_sp().code
    window_range = _get_window_range(request)

    oreqs = OrderRequest.objects.filter(supply_point__code=sp_code, date__range=window_range)
    eo_map = SortedDict()
    eos = 0
    total = 0
    max_val = 0
    for oreq in oreqs:
        total += oreq.total
        eos += oreq.emergency
        eo_map[oreq.product] = {}
        eo_map[oreq.product]['emergency'] = eos
        eo_map[oreq.product]['total'] = total
        if total > max_val:
            max_val = total

    # fake test data delete this ######
    eo_map = SortedDict()
    for product in Product.objects.all():
        eo_map[product] = {}
        eo_map[product]['emergency'] = random()*50
        eo_map[product]['total'] = eo_map[product]['emergency']*(random()+1)
        eo_map[product]['pct'] = pct(eo_map[product]['emergency'], eo_map[product]['total'])
        max_val = 100
    # end test data ####### 

    ret_obj = {}
    summary = {
        "number": 0,
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": max_val,
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "Products",
        "yaxistitle": "Orders"
    }
    
    # for label in ['pct']:
    for label in ['emergency', 'total']:
        summary["number"] += 1

        product_codes = []
        count = 0

        data_map = {}
        data_map[label] = []
        
        for eo in eo_map.keys():
            count += 1
            product_codes.append([count, '<span>%s</span>' % (str(eo.code.lower()))])
            data_map[label].append([count, eo_map[eo][label]])
        
        summary['data'].append({"label": label, "data": data_map[label]})

    summary['xlabels'] = product_codes

    table = {
        "title": "%HSA with Emergency Order by Product",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 35, 41, 53, 34], ['dt', 26, 26, 44, 21], ['sr', 84, 24, 54, 36]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['LA 1x6', 'LA 2x6']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['summary'] = summary
    ret_obj['table'] = table
    ret_obj['line'] = line_chart
    return ret_obj


def ofr_context(request):
    ret_obj = {}

    table1 = {
        "title": "Monthly Average OFR by Product (%)",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 32, 41, 54, 35], ['dt', 23, 22, 41, 16], ['sr', 45, 44, 74, 26]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "OFR for Selected Time Period by Facility and Product (%)",
        "header": ["Facility", "bi", "cl", "cf", "cm"],
        "data": [[3, 3, 4, 5, 3], [2, 2, 2, 4, 1], [4, 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['LA 1x6', 'LA 2x6']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def rsqr_context(request):
    ret_obj = {}

    table = {
        "title": "All Products (Aggregated Quantity required to ensure that HC can resupply",
        "header": ["Facility Name", "%HSA with Stockout", "LA 1x6", "LA 2x6", "Zinc"],
        "data": [['BULA', 32, 4123, 512, 3123], ['Chesamu', 22, 2123, 423, 123], ['Chikwina', 45, 4123, 423, 612]],
        "cell_width": "135px",
    }

    ret_obj['table'] = table
    return ret_obj

def as_context(request):
    ret_obj = {}

    table = {
        "title": "Current Alert Summary",
        "header": ["Facility", "# HSA", "%HSA stocked out", "%HSA with EO", "%HSA with no Products"],
        "data": [['BULA', 332, 42, 53, 35], ['Chesamu', 232, 25, 41, 11], ['Chikwina', 443, 41, 41, 46]],
        "cell_width": "135px",
    }
    
    ret_obj['table'] = table
    return ret_obj

def cp_context(request):
    ret_obj = {}

    table1 = {
        "title": "District Consumption Profiles",
        "header": ["Product", "Total Calc Cons", "Av Rep Rate", "AMC", "Total SOH"],
        "data": [['cc', 312, "47%", 5, 354], ['dt', 1322, "21%", 4, 121], ['sr', 4123, "14%", 4, 634]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Facility Consumption Profiles",
        "header": ["Product", "Total Calc Cons", "Av Rep Rate", "AMC", "Total SOH"],
        "data": [['cc', 3234, "40%", 5, 345], ['dt', 2123, "52%", 4, 111], ['sr', 4132, "43%", 4, 634]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['Av Monthly Cons', 'Av Months of Stock']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def ss_context(request):
    ret_obj = {}
    summary = {
        "number": 3,
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "products",
        "yaxistitle": "amount"
    }
    
    product_codes = []

    count = 0
    for product in Product.objects.all().order_by('sms_code')[0:10]:
        count += 1
        product_codes.append([count, '<span>%s</span>' % (str(product.code.lower()))])
        
    summary['xlabels'] = product_codes
    
    summary['data'] = barseries(['Stocked Out','Under Stock','Adequate'], 10)

    table1 = {
        "title": "",
        "header": ["Product", "HSA Stocked Out", "HSA Under", "HSA Adequate", "Overstock"],
        "data": [['cc', 34, 45, 52, 31], ['dt', 21, 25, 44, 17], ['sr', 43, 44, 41, 67]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "HSA Current Stock Status by District",
        "header": ["District", "HSA Stocked Out", "HSA Under", "HSA Adequate", "Overstock"],
        "data": [['cc', 33, 45, 52, 31], ['dt', 21, 29, 45, 13], ['sr', 43, 42, 42, 61]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['LA 1x6', 'LA 2x6']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['summary'] = summary
    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def lt_context(request):
    month_table = {
        "title": "",
        "header": ['Month', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
        "data": [['Jan', 3, 14, 7], ['Feb', 12, 7, 4], ['Mar', 14, 6, 4]],
    }

    lt_table = {
        "title": "Average Lead Times by Facility",
        "header": ['Facility', 'Period (# Months)', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
        "data": [['BULA', 6, 31, 42, 37], ['Chesamu', 6, 212, 27, 14], ['Chikwina', 6, 143, 61, 14]],
    }    
    return {"summary": timechart(['Ord-Ord Ready', 'Ord-Ord Received']),
            "month_table": month_table,
            "lt_table": lt_table}

def rr_context(request):
    ret_obj = {}
    shared_headers = ["% Reporting", "% Rep on time", "% Late Rep", "% No Rep", "% Complete"]
    shared_slugs = ["reported", "on_time", "late", "missing", "complete"]
    
    # reporting rates by month table
    sp = SupplyPoint.objects.get(location=request.location) \
        if request.location else get_country_sp()
    months = SortedDict()
    for year, month in months_between(request.datespan.startdate, 
                                      request.datespan.enddate):
        dt = datetime(year, month, 1)
        months[dt] = ReportingRate.objects.get(supply_point=sp, date=dt)
    
    month_data = [[dt.strftime("%B")] + [getattr(rr, "pct_%s" % k) for k in shared_slugs] \
                  for dt, rr in months.items()]
    
    ret_obj['month_table'] = {
        "title": "",
        "header": ["Months"] + shared_headers,
        "data": month_data,
    }

    def _avg_report_rate_table_data(queryset, startdate, enddate):
        datamap = SortedDict()
        for sp in queryset:
            spdata = defaultdict(lambda: 0)
            for year, month in months_between(startdate, 
                                              enddate):
                rr = ReportingRate.objects.get(supply_point=sp,
                                               date=datetime(year, month, 1))
                spdata['total'] += rr.total
                for k in shared_slugs:
                    spdata[k] += getattr(rr, k)
            datamap[sp] = spdata
                    
        return [[sp.name] + [fmt_pct(data[k], data['total']) for k in shared_slugs] \
                for sp, data in datamap.items()]
    
    # district breakdown
        
    ret_obj['district_table'] = {
        "title": "Average Reporting Rate (Districts)",
        "header": ["Districts"] + shared_headers,
        "data": _avg_report_rate_table_data(get_district_supply_points().order_by('name'), 
                                            request.datespan.startdate,
                                            request.datespan.enddate)
    }
    
    # facility breakdown
    if sp.type.code == config.SupplyPointCodes.DISTRICT:
        ret_obj['facility_table'] = {
            "title": "Average Reporting Rate (Facilities)",
            "header": ["Facilities"] + shared_headers,
            "data": _avg_report_rate_table_data\
                (facility_supply_points_below(sp.location).order_by('name'),
                 request.datespan.startdate,
                 request.datespan.enddate)
        }
    
    # chart
    ret_obj['graphdata'] = get_reporting_rates_chart(request.location, 
                                                     request.datespan.startdate, 
                                                     request.datespan.enddate)
    return ret_obj

def hsas(request):
    context = {}
    return render_to_response('malawi/new/hsas.html', context, context_instance=RequestContext(request))

def user_profiles(request):
    context = {}
    return render_to_response('malawi/new/user-profiles.html', context, context_instance=RequestContext(request))

def _get_window_date(request):
    # the window date is assumed to be the end date
    date = request.datespan.enddate
    assert date.day == 1
    return date

def _get_window_range(request):
    # the window date is assumed to be the end date
    date1 = request.datespan.startdate
    if not request.GET.get('from'):
        date1 = datetime(date1.year, (date1.month%12 - 2)%12 , 1)
    date2 = request.datespan.enddate
    assert date1.day == 1
    assert date2.day == 1
    return (date1, date2)

