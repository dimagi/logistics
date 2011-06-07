from django.core.urlresolvers import reverse

class ReportDefinition(object):
    """
    A configuration object to hold a report definition.
    
    This object expects you to have a corresponding function in 
    reportcalcs.py that contains metadata associated with the report.
    
    The docstring of the function is used as the report description.
    The function itself is used to render the report data.
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
        # TODO: genericize
        return "malawi_monitoring_report"
    
    @property
    def template(self):
        """
        The place where this report goes to look for a template.
        """
        # TODO: don't hard code the folder reference
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
        # TODO: genericize
        import logistics.apps.malawi.reportcalcs as reportcalcs
        return getattr(reportcalcs, self.slug)
    
class ReportInstance(object):
    """
    An instance of a report. Right now consists only of a pairing of 
    the report definition with a datespan representing the range to
    run the report on.
    """
    
    def __init__(self, definition, datespan):
        self.definition = definition
        self.datespan = datespan
    
    def get_report_body(self):
        """
        The body of the report, as html suitable for putting in a template
        """
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
    
