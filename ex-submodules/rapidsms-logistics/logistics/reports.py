from datetime import datetime, timedelta
from django.db.models.query_utils import Q
from rapidsms.models import Contact
from logistics.apps.logistics.models import ProductReport
from logistics.apps.logistics.const import Reports

class PieChartData():
    
    def __init__(self, title, data):
        self.title = title
        self.data = data
        
class ReportingBreakdown():
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
        
    