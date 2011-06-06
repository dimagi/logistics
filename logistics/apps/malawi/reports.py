from django.core.urlresolvers import reverse

class ReportConfig(object):
    """
    A configuration object to hold a report definition.
    """
    
    def __init__(self, slug, description):
        self.slug = slug
        self.description = description

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
    
class ReportInstance(object):
    def __init__(self, definition, datespan):
        self.definition = definition
        self.datespan = datespan
    
    def get_report_body(self):
        """
        Expects that you have a function defined in reportcalcs to match
        the slug
        """
        import logistics.apps.malawi.reportcalcs as reportcalcs
        return getattr(reportcalcs, self.definition.slug)(self) 
    
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
    
MONITORING_REPORTS = {
    "em_late_reporting":            ReportConfig("em_late_reporting", "HSAs who reported late (after 2nd of the month), by District"),
    "hsas_reporting":               ReportConfig("hsas_reporting", "HSAs who reported at least once in the past 30 days, by District and group"),
    "reporting_completeness":       ReportConfig("reporting_completeness", "HSA orders that are complete, by District  and group"),
    "fully_stocked_hsas":           ReportConfig("fully_stocked_hsas", "No stock outs reported in past 30 days by HSAs by product, by District and group"),
    "fully_stocked_facilities":     ReportConfig("fully_stocked_facilities", "No stock outs reported by HCs in past 30 days by product, by District and group"),
    "hsa_stockout_duration":        ReportConfig("hsa_stockout_duration", "Duration of HSA stockout by product over past 30 days (# days), by District and group"),
    "facility_stockout_duration":   ReportConfig("facility_stockout_duration", "Duration of HC stockout by product over past 30 days (# days), by District and group"),
    "emergency_orders":             ReportConfig("emergency_orders", "Emergency orders reported by HSAs, by District and group"),
    "order_discrepancies":          ReportConfig("order_discrepancies", "HSA orders with discrepency between order and receipt by product, by District and group"),
    "order_messages":               ReportConfig("order_messages", "List of order messages sent by cStock to HC in past 30 days, by HC, by time period"),
    "order_times":                  ReportConfig("order_times", "Time between HSA order and receipt, by District and group (hours) "),
    "hsas_with_stock":              ReportConfig("hsas_with_stock", "HSA with adequate stock, by District and group"),
    "average_discrepancies":        ReportConfig("average_discrepancies", "Average discrepancy  between order and receipt in past 30 days per product, by District"),
}