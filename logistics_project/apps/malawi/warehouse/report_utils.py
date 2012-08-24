import json
from copy import deepcopy
from datetime import datetime
from collections import defaultdict
from random import random

from dimagi.utils.dates import months_between, add_months, DateSpan
from dimagi.utils.decorators.datespan import datespan_in_request

from logistics.reports import ProductAvailabilitySummary, Colors
from logistics.models import Product, SupplyPoint

from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData,\
    ReportingRate
from logistics_project.apps.malawi.util import get_country_sp, pct


class WarehouseProductAvailabilitySummary(ProductAvailabilitySummary):
    """
    Product availability summary, coming from the Malawi data warehouse models.
    
    This version also includes new categories under and over stock and is
    by percentage instead of by absolute number.
    """
    def __init__(self, supply_point, date, width=900, height=300):
        """
        Override the ProductAvailabilitySummary object to work off 
        the warehouse tables.
        """
        self._width = width
        self._height = height
        self._date = date
        self._supply_point = supply_point
        
        
        products = Product.objects.all().order_by('sms_code')
        data = []
        for p in products:
            availability_data = ProductAvailabilityData.objects.get\
                (supply_point=supply_point, date=date, product=p)
            
            data.append({"product": p,
                         "total": availability_data.managed,
                         "without_stock": availability_data.managed_and_without_stock,
                         "under_stock": availability_data.managed_and_under_stock,
                         "good_stock": availability_data.managed_and_good_stock,
                         "over_stock": availability_data.managed_and_over_stock,
                         "without_data": availability_data.managed_and_without_data})
        self.data = data
    
    @property
    def max_value(self):
        # since it's a percent
        return 100

    @property
    def yaxistitle(self):
        # TODO - can customize this if necessary
        return "% of HSAs"
        

    _flot_data = None
    @property
    def flot_data(self):

        if self._flot_data is None:
            without_stock = []
            under_stock = []
            good_stock = []
            over_stock = []
            without_data = []
            products = []
            for i, product_summary in enumerate(self.data):
                index = i + 1
                under_stock.append([index, pct(product_summary["under_stock"],
                                                product_summary["total"])])
                good_stock.append([index, pct(product_summary["good_stock"],
                                               product_summary["total"])])
                over_stock.append([index, pct(product_summary["over_stock"],
                                               product_summary["total"])])
                without_stock.append([index, pct(product_summary["without_stock"],
                                                  product_summary["total"])])
                without_data.append([index, pct(product_summary["without_data"],
                                                 product_summary["total"])])
                products.append([index, "<span title='%s'>%s</span>" % \
                                        (product_summary["product"].name, 
                                         product_summary["product"].sms_code)])

            bar_data = [{"data" : without_stock,
                         "label": "Stocked out",
                         "bars": { "show" : "true"},
                         "color": Colors.DARK_RED,
                        },
                        {"data" : under_stock,
                         "label": "Under stock",
                         "bars": { "show" : "true"},
                         "color": Colors.MEDIUM_YELLOW,
                         
                        },
                        {"data" : good_stock,
                         "label": "Adequate stock",
                         "bars": { "show" : "true"},
                         "color": Colors.MEDIUM_GREEN,
                         
                        },
                        {"data" : over_stock,
                         "label": "Overstocked",
                         "bars": { "show" : "true"},
                         "color": Colors.MEDIUM_PURPLE,
                         
                        },
                        {"data" : without_data,
                         "label": "No Stock Data",
                         "bars": { "show" : "true"},
                         "color": Colors.LIGHT_GREY,
                        }]
            self._flot_data = {"data": json.dumps(bar_data),
                               "ticks": json.dumps(products)}
                
        return self._flot_data

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

def get_reporting_rates_chart(location, start, end):

    uniq_id = "%d" % (random()*10000)
    report_chart = {
        "legenddiv": "summary-legend-div-" + uniq_id,
        "div": "summary-chart-div-" + uniq_id,
        "max_value": 100,
        "width": "100%",
        "height": "200px",
        "xaxistitle": "month",
    }
    data = defaultdict(lambda: defaultdict(lambda: 0)) # turtles!
    dates = []
    sp = SupplyPoint.objects.get(location=location) if location else get_country_sp()
    for year, month in months_between(start, end):
        dt = datetime(year, month, 1)
        dates.append(dt)
        rr = ReportingRate.objects.get(supply_point=sp, date=dt)
        data["on time"][dt] = pct(rr.on_time, rr.total)
        data["late"][dt] = pct(rr.reported - rr.on_time, rr.total)
        data["missing"][dt] = pct(rr.total - rr.reported, rr.total)
        data["complete"][dt] = pct(rr.complete, rr.total)
    
    ret_data = [{'data': [[i + 1, data[k][dt]] for i, dt in enumerate(dates)],
                 'label': k, 'lines': {"show": False}, "bars": {"show": True},
                 'stack': 0} \
                 for k in ["on time", "late", "missing"]]
    
    ret_data.append({'data': [[i + 1, data["complete"][dt]] for i, dt in enumerate(dates)],
                     'label': 'complete', 'lines': {"show": True}, "bars": {"show": False},
                     'yaxis': 2})
    
    report_chart['xlabels'] = [[i + 1, '%s' % dt.strftime("%b")] for i, dt in enumerate(dates)]
    report_chart['data'] = json.dumps(ret_data)
    report_chart['number'] = 3
    return report_chart


def current_report_period():
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)

def get_window_date(request):
    # the window date is assumed to be the end date
    date = request.datespan.enddate
    assert date.day == 1
    return date

def get_window_range(request):
    date1 = request.datespan.startdate
    if not request.GET.get('from'):
        date1 = datetime(date1.year, (date1.month%12 - 2)%12 , 1)
    date2 = request.datespan.enddate
    assert date1.day == 1
    assert date2.day == 1
    return (date1, date2)

def increment_dict_item(dictionary, key, val):
    if dictionary.has_key(key):
        dictionary[key] += val
    else:
        dictionary[key] = val
    return dictionary

def list_key_values(dictionary, key_list=None):
    if not key_list:
        key_list = dictionary.keys()
    return [dictionary[key] for key in key_list if dictionary.has_key(key)]

def sum_of_key_values(dictionary, key_list):
    return sum(list_key_values(dictionary, key_list)) 

def avg_of_key_values(dictionary, key_list):
    total = sum_of_key_values(dictionary, key_list)
    count = 0
    for key in key_list:
        if dictionary.has_key(key):
            count += 1
    return pct(total, count) / 100

def get_datelist(start, end):
    return [datetime(year, month, 1)\
            for year, month in months_between(start, end)]

def remove_zeros_from_dict(dicti, key_val):
    dictionary = deepcopy(dicti)
    if dictionary.has_key(key_val):
        if dictionary[key_val] == 0 or not dictionary[key_val]:
            dictionary.pop(key_val)
            return dictionary, True
    for key in dictionary.keys():
        if isinstance(dictionary[key], dict):
            if _remove_zeros_from_dict(dictionary[key], key_val)[1]:
                dictionary.pop(key)
    return dictionary, False

def month_labels(start_date, end_date):
    return [[i + 1, '<span>%s</span>' % datetime(year, month, 1).strftime("%b")] \
            for i, (year, month) in enumerate(months_between(start_date, end_date))]

def get_hsa_url(hsa):
    return '/malawi/r/hsas/?hsa_code=%s' % hsa.code

