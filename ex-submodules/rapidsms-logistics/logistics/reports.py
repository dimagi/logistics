from datetime import timedelta
from rapidsms.models import Contact
from logistics.apps.logistics.models import ProductReport, Product, ProductStock,\
    SupplyPoint
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.tables import ReportingTable
import json
from django.core.urlresolvers import reverse
import logistics.apps.logistics.models as logistics_models
from logistics.apps.logistics.util import DateSpan

class Colors(object):
    RED = "red"
    GREEN = "green"
    PURPLE = "#8b198b"
    LIGHT_RED = "#ff9899"
    LIGHT_GREEN = "#9acc99"
    LIGHT_PURPLE = "#bf7ebe"
    LIGHT_YELLOW = "#fff6cf"
    MEDIUM_GREEN = "#7aaa7a"
    MEDIUM_PURPLE = "#a460a4"
    MEDIUM_YELLOW = "#efde7f"
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

class ReportingBreakdown(object):
    """
    Given a query set of supply points, get an object for displaying reporting
    information.
    """
    
    def __init__(self, supply_points, datespan=None, include_late=False, 
                 days_for_late = 5):
        self.supply_points = supply_points
        
        if datespan == None:
            datespan = DateSpan.since(30)
        self.datespan = datespan
        
        self.include_late = include_late
        self.days_for_late = days_for_late
        date_for_late = datespan.startdate + timedelta(days=days_for_late)
        
        reports_in_range = ProductReport.objects.filter\
            (report_type__code=Reports.SOH,
             report_date__gte=datespan.startdate,
             report_date__lte=datespan.enddate,
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
        
        
        # fully reporting / non reporting
        full = []
        partial = []
        unconfigured = []
        for sp in reported.all():
            
            # makes an assumption of 1 contact per SP.
            # will need to be revisited
            contact = Contact.objects.get(supply_point=sp)
            found_reports = reports_in_range.filter(supply_point=sp)
            found_products = set(found_reports.values_list("product", flat=True).distinct())
            needed_products = set([c.pk for c in contact.commodities.all()])
            if needed_products:
                if needed_products - found_products:
                    partial.append(sp)
                else:
                    full.append(sp)
            else:
                unconfigured.append(sp)
        
        self.full = full
        self.partial = partial
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
                {"display": "Fully Reported",
                 "value": len(self.full),
                 "color": Colors.LIGHT_GREEN,
                 "description": "(%s) %s in %s" % \
                    (len(self.full), "Fully reported", self.datespan)
                },
                {"display": "Partially Reported",
                 "value": len(self.partial),
                 "color": Colors.MEDIUM_PURPLE,
                 "description": "(%s) %s in %s" % \
                    (len(self.partial), "Partially reported", self.datespan)
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
        return [TableData("Incomplete Reports", ReportingTable(self.partial)),
                TableData("Complete Reports", ReportingTable(self.full)),
                TableData("HSAs not associated to supplied products", ReportingTable(self.unconfigured))]
        
    _on_time_chart = None
    def on_time_chart(self):
        if self._on_time_chart is None:
            graph_data = [
                {"display": "On Time",
                 "value": len(self.on_time),
                 "color": Colors.LIGHT_GREEN,
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
            self._on_time_chart = PieChartData("Reporting Rates (%s)" % self.datespan, graph_data)
        return self._on_time_chart
        
    def on_time_groups(self):
        if self.include_late:
            [TableData("Non-Reporting HSAs", ReportingTable(self.non_reporting)),
             TableData("Late HSAs", ReportingTable(self.late)),
             TableData("On-Time HSAs", ReportingTable(self.on_time))]
        else:
            return [TableData("Non-Reporting HSAs", ReportingTable(self.non_reporting)),
                    TableData("On-Time HSAs", ReportingTable(self.on_time))]

class ProductAvailabilitySummary(object):
    
    def __init__(self, contacts, width=900, height=300):
        """
        contacts should be a query set of contacts that you care about
        the product availability for.
        
        This currently assumes a 1:1 ratio of contact to supply points
        """
        self._width = width
        self._height = height
        
        products = Product.objects.all()
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
        return "Number of HSAs"
    
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
                products.append([index, product_summary["product"].sms_code])

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
        val = getattr(logistics_models, name)(self.facility_list, self.commodity_filter, self.commoditytype_filter)
        self._cached_stock[name] = val
        return val
    
    def stockout_count(self): return self._call_stock_count("stockout_count")
    def emergency_stock_count(self): return self._call_stock_count("emergency_stock_count")
    def adequate_supply_count(self): return self._call_stock_count("adequate_supply_count")
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
