import json
from datetime import timedelta, datetime
from django.core.urlresolvers import reverse
from django.db.models.expressions import F
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.db.models import Q
from django.utils.importlib import import_module
from rapidsms.conf import settings
from dimagi.utils.dates import DateSpan
from logistics.models import ProductReport, \
    Product, ProductStock, SupplyPoint, StockRequest, HistoricalStockCache
from .tables import SOHReportingTable
from .const import Reports
from .util import config

if hasattr(settings, 'LOGISTICS_CONFIG'):
    config = import_module(settings.LOGISTICS_CONFIG)
else:
    import config

class Colors(object):
    RED = "red"
    GREEN = "green"
    PURPLE = "#8b198b"
    LIGHT_RED = "#ff9899"
    LIGHT_GREEN = "#9acc99"
    LIGHT_PURPLE = "#bf7ebe"
    LIGHT_YELLOW = "#fff6cf"
    LIGHT_GREY = "#dddddd"
    MEDIUM_GREEN = "#7aaa7a"
    MEDIUM_PURPLE = "#a460a4"
    MEDIUM_YELLOW = "#efde7f"
    MEDIUM_GREY = "#999999"
    DARK_RED = "#a30808"
    WHITE = "#ffffff"
    BLACK = "#000000"
    
    
class PieChartData(object):
    
    def __init__(self, title, data):
        self.title = title
        self.data = data
        
class TableData(object):
    
    def __init__(self, title, table):
        self.title = title
        self.table = table

def _seconds(td):
    """
    Because timedelta.total_seconds() is 2.7+ only.
    """
    return td.days * 24 * 60 * 60 + td.seconds

class ReportingBreakdown(object):
    """
    Given a query set of supply points, get an object for displaying reporting
    information.
    """
    
    def __init__(self, supply_points, datespan=None, include_late=False,
                 days_for_late=5, MNE=False, request=None):
        
        self.supply_points = supply_points = supply_points.filter(active=True)
        
        if not datespan:
            datespan = DateSpan.since(30)
        self.datespan = datespan
        
        self._request = request
        self.include_late = include_late
        self.days_for_late = days_for_late
        date_for_late = datespan.startdate + timedelta(days=days_for_late)
        
        reports_in_range = ProductReport.objects.filter\
            (report_type__code=Reports.SOH,
             report_date__gte=datespan.startdate,
             report_date__lte=datespan.enddate_param,
             supply_point__in=supply_points)
        
        reported_in_range = reports_in_range.values_list\
            ("supply_point", flat=True).distinct()
        
        reported_on_time_in_range = reports_in_range.filter\
            (report_date__lte=date_for_late).values_list\
            ("supply_point", flat=True).distinct()
        
        non_reporting = supply_points.exclude(pk__in=reported_in_range)
        reported = SupplyPoint.objects.filter(pk__in=reported_in_range)
        reported_late = reported.exclude(pk__in=reported_on_time_in_range)
        reported_on_time = SupplyPoint.objects.filter\
            (pk__in=reported_on_time_in_range)

        requests_in_range = StockRequest.objects.select_related().filter(\
            requested_on__gte=datespan.startdate,
            requested_on__lte=datespan.enddate,
            supply_point__in=supply_points
        )

        if MNE:
            emergency_requests = requests_in_range.filter(is_emergency=True)

            emergency_requesters = emergency_requests.values_list("supply_point", flat=True).distinct()

            filled_requests = requests_in_range.exclude(received_on=None).exclude(status='canceled')
            discrepancies = filled_requests.exclude(amount_requested=F('amount_received'))
            discrepancies_list = discrepancies.values_list("product", flat=True) #not distinct!
            orders_list = filled_requests.values_list("product", flat=True)

            # We could save a lot of time here if the primary key for Product were its sms_code.
            # Unfortunately, it isn't, so we have to remap keys->codes.
            _p = {}
            for p in Product.objects.filter(pk__in=orders_list.distinct()): _p[p.pk] = p.sms_code
            def _map_codes(dict):
                nd = {}
                for d in dict:
                    nd[_p[d]] = dict[d]
                return nd

            # Discrepancies are defined as a difference of 20% or more in an order.

            self.discrepancies_p = {}
            self.discrepancies_tot_p = {}
            self.discrepancies_pct_p = {}
            self.discrepancies_avg_p = {}
            self.filled_orders_p = {}
            for product in orders_list.distinct():
                self.discrepancies_p[product] = len(filter(lambda r: (r.amount_received >= (1.2 * r.amount_requested) or
                                                                      r.amount_received <= (.8 * r.amount_requested)), 
                                                                      [x for x in discrepancies if x.product.pk == product]))

                z = [r.amount_requested - r.amount_received for r in \
                     discrepancies.filter(product__pk=product)]
                self.discrepancies_tot_p[product] = sum(z)
                if self.discrepancies_p[product]: 
                    self.discrepancies_avg_p[product] = \
                        self.discrepancies_tot_p[product] / self.discrepancies_p[product]
                
                self.filled_orders_p[product] = len([x for x in orders_list if x == product])
                self.discrepancies_pct_p[product] = calc_percentage\
                    (self.discrepancies_p[product], self.filled_orders_p[product])


            self.discrepancies_p = _map_codes(self.discrepancies_p)
            self.discrepancies_tot_p = _map_codes(self.discrepancies_tot_p)
            self.discrepancies_pct_p = _map_codes(self.discrepancies_pct_p)
            self.discrepancies_avg_p = _map_codes(self.discrepancies_avg_p)
            self.filled_orders_p = _map_codes(self.filled_orders_p)


            self.avg_req_time = None
            self.req_times = []
            if filled_requests:
                secs = [_seconds(f.received_on - f.requested_on) for f in filled_requests]
                self.avg_req_time = timedelta(seconds=(sum(secs) / len(secs)))
                self.req_times = secs

        # fully reporting / non reporting
        full = []
        partial = []
        unconfigured = []
        stockouts = []
        no_stockouts = []
        no_stockouts_p = {}
        stockouts_p = {}
        totals_p = {}
        stockouts_duration_p = {}
        stockouts_avg_duration_p = {}
        for sp in reported.all():
            
            found_reports = reports_in_range.filter(supply_point=sp)
            found_products = set(found_reports.values_list("product", flat=True).distinct())
            needed_products = set([c.pk for c in sp.commodities_stocked()])
            if needed_products:
                if needed_products - found_products:
                    partial.append(sp)
                else:
                    full.append(sp)
            else:
                unconfigured.append(sp)
            if MNE:
                prods = Product.objects.filter(pk__in=list(found_products))
                for p in prods:
                    if not p.code in stockouts_p: stockouts_p[p.sms_code] = 0
                    if not p.code in no_stockouts_p: no_stockouts_p[p.sms_code] = 0
                    if not p.code in totals_p: totals_p[p.sms_code] = 0
                    if found_reports.filter(product=p, quantity=0):
                        stockouts_p[p.sms_code] += 1
                    else:
                        no_stockouts_p[p.sms_code] += 1
                    totals_p[p.sms_code] += 1

                if found_reports.filter(quantity=0):
                    stockouts.append(sp.pk)
#                    prods = found_reports.values_list("product", flat=True).distinct()
                    for p in prods:
                        duration = 0
                        count = 0
                        last_stockout = None
                        ordered_reports = found_reports.filter(product=p).order_by("report_date")
                        if ordered_reports.count():
                            # Check if a stockout carried over from last period.
                            last_prev_report = ProductReport.objects.filter(product=p,
                                                                            supply_point=sp,
                                                                            report_date__lt=ordered_reports[0].report_date).order_by("-report_date")
                            if last_prev_report.count() and last_prev_report[0].quantity == 0:
                                last_stockout = datespan.startdate

                            # Check if a stockout carries over into next period.


                        for r in ordered_reports:
                            if last_stockout and r.quantity > 0: # Stockout followed by receipt.
                                duration += _seconds(r.report_date - last_stockout)
                                last_stockout = None
                                count += 1
                            elif not last_stockout and r.quantity == 0: # Beginning of a stockout period.
                                last_stockout = r.report_date
                            else: # In the middle of a stock period, or the middle of a stockout period; either way, we don't care.
                                pass

                        if last_stockout:
                            first_next_report = ProductReport.objects.filter(product=p,
                                supply_point=sp,
                                quantity__gt=0,
                                report_date__gt=ordered_reports.order_by("-report_date")[0].report_date)
                            if first_next_report.count() and first_next_report[0].quantity > 0:
                                duration += _seconds(datespan.enddate - last_stockout)

                        if p.sms_code in stockouts_duration_p and duration:
                            stockouts_duration_p[p.sms_code] += [duration]
                        elif duration:
                            stockouts_duration_p[p.sms_code] = [duration]
                else:
                    no_stockouts.append(sp.pk)
        if MNE:
            no_stockouts_pct_p = {}

            for key in no_stockouts_p:
                if totals_p[key] > 0:
                    no_stockouts_pct_p[key] = calc_percentage(no_stockouts_p[key], totals_p[key])

            for key in stockouts_duration_p:
                stockouts_avg_duration_p[key] = timedelta(seconds=sum(stockouts_duration_p[key]) / len(stockouts_duration_p[key]))

            self.stockouts = stockouts
            self.emergency = emergency_requesters
            self.stockouts_emergency = set(stockouts).intersection(set(emergency_requesters))
            self.stockouts_p = stockouts_p
            self.no_stockouts_pct_p = no_stockouts_pct_p
            self.no_stockouts_p = no_stockouts_p
            self.totals_p = totals_p
            self.stockouts_duration_p = stockouts_duration_p
            self.stockouts_avg_duration_p = stockouts_avg_duration_p
        # ro 10/14/11 - not sure why querysets are necessary. 
        # something changed in the djtables tables spec with the new ordering features?
        self.full = SupplyPoint.objects.filter(pk__in=[f.pk for f in full])
        self.partial = SupplyPoint.objects.filter(pk__in=[p.pk for p in partial])
        self.unconfigured = unconfigured
        
        self.non_reporting = non_reporting
        self.reported = reported
        self.reported_on_time = reported_on_time
        self.reported_late = reported_late

    @property
    def on_time(self):
        """
        If we care about whether someone reported late versus
        at all, then treat this differently. 
        """
        if self.include_late:
            return self.reported_on_time    
        else:
            return self.reported
        
    _breakdown_chart = None
    def breakdown_chart(self):
        if self._breakdown_chart is None:
            graph_data = [
                {"display": "Comp. Reports",
                 "value": len(self.full),
                 "color": Colors.GREEN,
                 "description": "(%s) %s in %s" % \
                    (len(self.full), "Complete Reports", self.datespan)
                },
                {"display": "Inc. Reports",
                 "value": len(self.partial),
                 "color": Colors.PURPLE,
                 "description": "(%s) %s in %s" % \
                    (len(self.partial), "Incomplete Reports", self.datespan)
                },
#                {"display": "Unconfigured",
#                 "value": len(self.unconfigured),
#                 "color": "red",
#                 "description": "Unconfigured for stock information"
#                }
            ]     
            self._breakdown_chart = PieChartData("Reporting Details (%s)" % self.datespan, graph_data)
        return self._breakdown_chart
        
    def breakdown_groups(self):
        return [TableData("Incomplete Reports", SOHReportingTable(object_list=self.partial,
                                                                  request=self._request,
                                                                  prefix='inc-',
            month=self.datespan.enddate.month,
            year=self.datespan.enddate.year,
            day=self.datespan.enddate.day)),
                TableData("Complete Reports", SOHReportingTable(object_list=self.full,
                                                                request=self._request,
                                                                  prefix='comp-',
                    month=self.datespan.enddate.month,
                    year=self.datespan.enddate.year,
                    day=self.datespan.enddate.day))
                #TableData("HSAs not associated to supplied products", ReportingTable(self.unconfigured, request=self._request))
                ]
        
    _on_time_chart = None
    def on_time_chart(self):
        if self._on_time_chart is None:
            graph_data = [
                {"display": "On Time" if self.include_late else "Reporting",
                 "value": len(self.on_time),
                 "color": Colors.GREEN, 
                 "description": "(%s) On Time (%s)" % \
                    (len(self.on_time), self.datespan)
                },
                {"display": "Non Reporting",
                 "value": len(self.non_reporting),
                 "color": Colors.RED,
                 "description": "(%s) Non-Reporting (%s)" % \
                    (len(self.non_reporting), self.datespan)
                }
            ]
            if self.include_late:
                graph_data += [
                        {"display": "Late Reporting",
                         "value": len(self.reported_late),
                         "color": Colors.PURPLE,
                         "description": "(%s) Late (%s)" % \
                            (len(self.reported_late), self.datespan)
                        }
                ]
            self._on_time_chart = PieChartData("Reporting Rates (%s)" % self.datespan, graph_data)
        return self._on_time_chart
        
    def on_time_groups(self):
        if self.include_late:
            return [TableData("Non-Reporting HSAs", SOHReportingTable(object_list=self.non_reporting,
                                                               request=self._request, 
                                                               prefix='nonreport-',
            month=self.datespan.enddate.month,
            year=self.datespan.enddate.year,
                day=self.datespan.enddate.day)),
             TableData("Late HSAs", SOHReportingTable(object_list=self.reported_late,
                                                      request=self._request, 
                                                      prefix='late-',
                 month=self.datespan.enddate.month,
                 year=self.datespan.enddate.year,
                 day=self.datespan.enddate.day)),
             TableData("On-Time HSAs", SOHReportingTable(object_list=self.on_time,
                                                         request=self._request, 
                                                         prefix='ontime-',
                 month=self.datespan.enddate.month,
                 year=self.datespan.enddate.year,
                 day=self.datespan.enddate.day))]
        else:
            return [TableData("Non-Reporting HSAs", SOHReportingTable(object_list=self.non_reporting,
                                                                      request=self._request, 
                                                                      prefix='nonreport-',
                month=self.datespan.enddate.month,
                year=self.datespan.enddate.year,
                day=self.datespan.enddate.day)),
                    TableData("Reporting HSAs", SOHReportingTable(object_list=self.on_time,
                                                                  request=self._request,
                                                                  prefix='report-',
                        month=self.datespan.enddate.month,
                        year=self.datespan.enddate.year,
                        day=self.datespan.enddate.day
                    ))]

class ProductAvailabilitySummary(object):

    def __init__(self, contacts, width=900, height=300):
        """
        contacts should be a query set of contacts that you care about
        the product availability for.
        
        This currently assumes a 1:1 ratio of contact to supply points
        """
        self._width = width
        self._height = height
        
        products = Product.objects.all().order_by('sms_code')
        data = []
        for p in products:
            supplying = contacts.filter(commodities=p)
            if supplying:
                total = supplying.count()
                supplying_sps = supplying.values_list("supply_point", flat=True)
                stocks = ProductStock.objects.filter(product=p, supply_point__pk__in=supplying_sps)
                with_stock = stocks.filter(quantity__gt=0).count()
                without_stock = stocks.filter(quantity=0).count()
                without_data = total - with_stock - without_stock
                data.append({"product": p,
                             "total": total,
                             "with_stock": with_stock,
                             "without_stock": without_stock,
                             "without_data": without_data})
        self.data = data
        
    @property
    def max_value(self):
        return max([d["total"] for d in self.data]) if self.data else 0
    
    @property
    def width(self):
        return self._width
    @property
    def height(self):
        return self._height
    
    @property
    def yaxistitle(self):
        # TODO - can customize this if necessary
        return config.Messages.NUMBER_OF_SUPPLY_POINTS
    
    @property
    def xaxistitle(self):
        # TODO - can customize this if necessary
        return "Products"
        
    @property
    def div(self):
        # TODO - can customize this if necessary
        return "product_availability_summary_plot_placeholder"
        
    @property
    def legenddiv(self):
        # TODO - can customize this if necessary
        return "product_availability_summary_legend"
        
    @property
    def legend_cols(self):
        """
        Number of columns to use in the legend. Defaults to 3 if not overridden.
        """
        return 3
        
    _flot_data = None
    @property
    def flot_data(self):
        if self._flot_data is None:
            with_stock = []
            without_stock = []
            without_data = []
            products = []
            for i, product_summary in enumerate(self.data):
                index = i + 1
                with_stock.append([index, product_summary["with_stock"]])
                without_stock.append([index, product_summary["without_stock"]])
                without_data.append([index, product_summary["without_data"]])
                products.append([index, "<span title='%s'>%s</span>" % (product_summary["product"].name, product_summary["product"].name)])

            bar_data = [{"data" : without_stock,
                         "label": "Stocked out",
                         "bars": { "show" : "true"},
                         "color": Colors.DARK_RED,
                        },
                        {"data" : with_stock,
                         "label": "Not Stocked out",
                         "bars": { "show" : "true"},
                         "color": Colors.MEDIUM_GREEN,
                         
                        },
                        {"data" : without_data,
                         "label": "No Stock Data",
                         "bars": { "show" : "true"},
                         "color": Colors.MEDIUM_YELLOW,
                        }]
            self._flot_data = {"data": json.dumps(bar_data),
                               "ticks": json.dumps(products)}
                
        return self._flot_data

class SidewaysProductAvailabilitySummary(ProductAvailabilitySummary):


    @property
    def height(self):
        return self._width
    @property
    def width(self):
        return self._height

    @property
    def flot_data(self):
        with_stock = []
        without_stock = []
        without_data = []
        products = []
        map = {}
        for i, product_summary in enumerate(self.data):
            index = i + 1
            with_stock.append([product_summary["with_stock"], index])
            without_stock.append([product_summary["without_stock"], index])
            without_data.append([product_summary["without_data"], index])
            map[product_summary['product'].sms_code] = {"index": index,
                                                        "name": product_summary["product"].name,
                                                        "with_stock": product_summary['with_stock'],
                                                        "without_stock": product_summary['without_stock'],
                                                        "without_data": product_summary['without_data'],
                                                        "tick": "<span title='%s'>%s</span>" % (product_summary["product"].name, product_summary["product"].sms_code)
                                                        }
            products.append(product_summary['product'].sms_code)
        bar_data = [{"data" : [],
                     "label": "Stocked out",
                     "bars": { "show" : "true"},
                     "color": Colors.DARK_RED,
                    },
                    {"data" : [],
                     "label": "Not Stocked out",
                     "bars": { "show" : "true"},
                     "color": Colors.MEDIUM_GREEN,
                    },
                    {"data" : [],
                     "label": "No Stock Data",
                     "bars": { "show" : "true"},
                     "color": Colors.MEDIUM_YELLOW,
                    }]

        self._flot_data = {"data": json.dumps(bar_data),
                           "products": json.dumps(products),
                           "dmap": json.dumps(map)}
        return self._flot_data

class ProductAvailabilitySummaryByFacility(ProductAvailabilitySummary):
    
    def __init__(self, facilities, width=900, height=300):
        """
        facilities should be a query set of facilities that you care about
        the product availability for.
        """
        self._width = width
        self._height = height
        
        products = Product.objects.all().order_by('sms_code')
        data = []
        for p in products:
            supplying_facilities = facilities.filter(contact__commodities=p).distinct()
            if supplying_facilities:
                total = supplying_facilities.count()
                stocks = ProductStock.objects.filter(product=p, supply_point__in=supplying_facilities)
                with_stock = stocks.filter(quantity__gt=0).count()
                without_stock = stocks.filter(quantity=0).count()
                without_data = total - with_stock - without_stock
                data.append({"product": p,
                             "total": total,
                             "with_stock": with_stock,
                             "without_stock": without_stock,
                             "without_data": without_data})
        self.data = data

class ProductAvailabilitySummaryByFacilitySP(ProductAvailabilitySummary):
    """ it looks like this is a slower but more full-featured version of 
    ProductAvailabilitySummaryByFacility which supports query by date, plus 
    some incomplete code for using caching looking ahead: could merge these 
    two functions, or replace this entirely with tanzania warehousing stuff
    """

    def __init__(self, facilities, width=900, height=300, month=None, year=None):
        """
        facilities should be a query set of facilities that you care about
        the product availability for.
        """
        if not (month and year):
            year = datetime.utcnow().year
            month = datetime.utcnow().month
        self._width = width
        self._height = height

        total = facilities.count()

        products = Product.objects.all().order_by('sms_code')
        data = []
        
        for p in products:

            # once we want to use the cache we can use these to populate
            # this object, but for now disable it
            if False:
                relevant = HistoricalStockCache.objects.filter(product=p,
                                                               year=year, 
                                                               month=month)
                with_stock = relevant.filter(stock__gt=0).count()
                without_stock = relevant.filter(stock=0).count()
                without_data = total - with_stock - without_stock
            else:
                # TODO This is ludicrously inefficient.
            
                with_stock = 0
                without_stock = 0
                without_data = 0
                for f in facilities:
                    stock = f.historical_stock(p, year, month, default_value=-1)
                    if stock > 0:
                        with_stock += 1
                    elif stock == 0:
                        without_stock += 1
                    else:
                        without_data += 1
            data.append({"product": p,
                         "total": total,
                         "with_stock": with_stock,
                         "without_stock": without_stock,
                         "without_data": without_data})
        self.data = data

class DynamicProductAvailabilitySummaryByFacilitySP(ProductAvailabilitySummaryByFacilitySP, SidewaysProductAvailabilitySummary):

    def __init__(self, facilities, width=900, height=360, month=None, year=None):
        super(DynamicProductAvailabilitySummaryByFacilitySP, self).__init__(facilities, width, height, month, year)

class SupplyPointRow():
        
    def __init__(self, supply_point, commodity_filter, commoditytype_filter):
        self.supply_point = supply_point
        self.commodity_filter = commodity_filter
        self.commoditytype_filter = commoditytype_filter
        self._cached_stock = {}
        
    @property
    def is_active(self):
        return self.supply_point.location.is_active
    
    @property
    def name(self):
        return self.supply_point.name
    
    @property 
    def code(self):
        return self.supply_point.code
    
    @property
    def url(self):
        """
        A url for this object.
        
        Must be overridden.
        """
        raise NotImplementedError()
        
    @property
    def facility_list(self):
        """
        The list of facilities to include in the stock counts for this object
        
        Must be overridden.
        """
        raise NotImplementedError()
        
    def _call_stock_count(self, name):
        if name in self._cached_stock:
            return self._cached_stock[name]
        
        val = sum(getattr(f, name)(product=self.commodity_filter,
                                   producttype=self.commoditytype_filter) for f in self.facility_list)
        self._cached_stock[name] = val
        return val
    
    def stockout_count(self): return self._call_stock_count("stockout_count")
    def emergency_stock_count(self): return self._call_stock_count("emergency_stock_count")
    def adequate_supply_count(self): return self._call_stock_count("adequate_supply_count")
    def emergency_plus_low(self): return self._call_stock_count("emergency_plus_low")
    def good_supply_count(self): return self._call_stock_count("good_supply_count")
    def overstocked_count(self): return self._call_stock_count("overstocked_count")
    
    @property
    def consumption(self): 
        if self.commodity_filter is not None:
            return self.supply_point.consumption(product=self.commodity_filter,
                                                 producttype=self.commoditytype_filter)
        
    

class HSASupplyPointRow(SupplyPointRow):
    
    @property
    def url(self):
        return reverse("malawi_hsa", args=[self.supply_point.code])

    @property
    def facility_list(self):
        # just talk about ourselves
        return [self.supply_point]
    


class FacilitySupplyPointRow(SupplyPointRow):
    
    @property
    def url(self):
        return reverse("malawi_facility", args=[self.supply_point.code])

    @property
    def facility_list(self):
        # aggregate over all children
        return self.supply_point.location.all_child_facilities()

def calc_percentage(a, b):
    if not (a and b):
        return 0 # Don't return ugly NaN
    return int((float(a) / float(b)) * 100.0)

def get_reporting_and_nonreporting_facilities(deadline, location):
    """
    Get all HSAs who haven't reported since a passed in date
    """
    if location is None:
        return None, None
    facilities = location.all_facilities()
    on_time_facilities = facilities.filter(last_reported__gte=deadline, active=True)
    late_facilities = facilities.filter(Q(last_reported=None) | Q(last_reported__lt=deadline), active=True)
    return on_time_facilities, late_facilities



class ReportView(object):
    """
    View class to be extended for each report page 
        with its own custom_context method
    
    Include in settings:

        REPORT_LIST = SortedDict([
        ("Dashboard", "dashboard"),])
    """
    _context = None
    
    def __init__(self, slug):
        self.slug = slug
        self._context = None
        
    @property
    def template_name(self):
        """
        The template that should be used for this.
        """
        # should be overridden
        return "%s.html" % self.slug
     
    def can_view(self, request):
        """
        Whether this report can be viewed - typically based of the user and 
        potentially other information in the request.
        """
        # should be overridden if you want to restrict things
        return True
    
    def get_response(self, request):
        """
        The HTTP Response object for this report
        """
        context = self.get_context(request)
        return render_to_response(self.template_name, 
                                  context,
                                  context_instance=RequestContext(request))

    
    def shared_context(self, request):
        """
        Add this to your subclasses shared_context method:

        base_context = super(<YourWarehouseViewSubclass>, self).shared_context(request)
        """
        to_stub = lambda x: {"name": x, "slug": settings.REPORT_LIST[x]}
        stub_reports = [to_stub(r) for r in settings.REPORT_LIST.keys()]

        return { 
            "report_list": stub_reports,
            "settings": settings
        }
        
    def custom_context(self, request):
        """
        Custom context required for a specific report
        """
        # should be overridden
        return {}
    
    def get_context(self, request):
        """
        Specific data to be included in a report
        """
        if not self._context:
            self._context = {"slug": self.slug}
            self._context.update(self.shared_context(request))
            self._context.update(self.custom_context(request))
        return self._context