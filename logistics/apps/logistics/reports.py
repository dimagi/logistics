from datetime import datetime, timedelta
from django.db.models.query_utils import Q
from rapidsms.models import Contact
from logistics.apps.logistics.models import ProductReport, Product, ProductStock
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.tables import ReportingTable
import json
from django.core.urlresolvers import reverse
import logistics.apps.logistics.models as logistics_models

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
    
    def __init__(self, supply_points, days=30):
        self.supply_points = supply_points
        self.days = days
        
        since  = datetime.utcnow() - timedelta(days=days)
    
        late = supply_points.filter(Q(last_reported__lt=since) | Q(last_reported=None)).order_by('-last_reported','name')
        on_time = supply_points.filter(last_reported__gte=since).order_by('-last_reported','name')
        
        # fully reporting / non reporting
        full = []
        partial = []
        unconfigured = []
        for sp in on_time.all():
            # makes an assumption of 1 contact per SP.
            # will need to be revisited
            contact = Contact.objects.get(supply_point=sp)
            found_reports = ProductReport.objects.filter(supply_point=sp, 
                                                         report_type__code=Reports.SOH,
                                                         report_date__gte=since)
            found_products = set(found_reports.values_list("product", flat=True))
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
        self.late = late
        self.on_time = on_time
        
        
    _breakdown_chart = None
    def breakdown_chart(self):
        if self._breakdown_chart is None:
            graph_data = [
                {"display": "Fully Reported",
                 "value": len(self.full),
                 "color": "green",
                 "description": "%s in last %s days" % ("Fully reported", self.days)
                },
                {"display": "Partially Reported",
                 "value": len(self.partial),
                 "color": "purple",
                 "description": "%s in last %s days" % ("Partially reported", self.days)
                },
                {"display": "Unconfigured",
                 "value": len(self.unconfigured),
                 "color": "red",
                 "description": "Unconfigured for stock information"
                }
            ]     
            self._breakdown_chart = PieChartData("Reporting Details (last %s days)" % self.days, graph_data)
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
                 "color": "green",
                 "description": "On Time in last %s days" % (self.days)
                },
                {"display": "Late",
                 "value": len(self.late),
                 "color": "red",
                 "description": "Late in last %s days" % (self.days)
                }
            ]     
            self._on_time_chart = PieChartData("Reporting Rates (last %s days)" % self.days, graph_data)
        return self._on_time_chart
        
    def on_time_groups(self):
        return [TableData("Non-Reporting HSAs", ReportingTable(self.late)),
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
                         "bars": { "show" : "true" },
                         "color": "red"  
                        },
                        {"data" : with_stock,
                         "label": "Not Stocked out", 
                         "bars": { "show" : "true" }, 
                         "color": "green"  
                        },
                        {"data" : without_data,
                         "label": "No Stock Data", 
                         "bars": { "show" : "true" }, 
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
    