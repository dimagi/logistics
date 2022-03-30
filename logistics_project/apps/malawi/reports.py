from __future__ import unicode_literals
from builtins import object
from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist


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
        import logistics_project.apps.malawi.reportcalcs as reportcalcs
        return getattr(reportcalcs, self.slug)
    
    @property
    def is_implemented(self):
        """
        Whether this report is implemented yet
        """
        # HACK! Don't say we're implemented until we have a template.
        try:
            get_template(self.template)
            return True
        except TemplateDoesNotExist:
            return False
    
        
class ReportInstance(object):
    """
    An instance of a report. Right now consists only of a pairing of 
    the report definition with a datespan representing the range to
    run the report on.
    """
    
    def __init__(self, definition, datespan, location=None):
        self.definition = definition
        self.datespan = datespan
        self.location = location
    
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
                "average_discrepancies",
                "amc_over_time"]

REPORTS_CURRENT = ["hsas_with_stock"]

REPORTS_LOCATION = ["order_messages"]
