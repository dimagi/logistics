from django.core.urlresolvers import reverse

class ReportDefinition(object):
    """
    A configuration object to hold a report definition.
    """
    
    def __init__(self, slug):
        self.slug = slug
        
    @property
    def url(self):
        """
        The URL for the report
        """
        return reverse(self.view_name, args=[self.slug])
    
    @property
    def view_name(self):
        """
        The name of the view for the report. 
        """
        return "malawi_monitoring_report"
    
    @property
    def template(self):
        return "malawi/partials/monitoring_reports/%s.html" % self.slug
    
    @property
    def description(self):
        return self.calcfunction.__doc__
    
    @property
    def calcfunction(self):
        """
        Expects that you have a function defined in reportcalcs to match
        the slug
        """
        import logistics.apps.malawi.reportcalcs as reportcalcs
        return getattr(reportcalcs, self.slug)
    
class ReportInstance(object):
    def __init__(self, definition, datespan):
        self.definition = definition
        self.datespan = datespan
    
    def get_report_body(self):
        return self.definition.calcfunction(self)
    
REPORT_SLUGS = ["em_late_reporting",
                "hsas_reporting",
                "reporting_completeness",
                "fully_stocked_hsas",
                "fully_stocked_facilities",
                "hsa_stockout_duration",
                "facility_stockout_duration",
                "emergency_orders",
                "order_discrepancies",
                "order_messages",
                "order_times",
                "hsas_with_stock",
                "average_discrepancies"]
    
