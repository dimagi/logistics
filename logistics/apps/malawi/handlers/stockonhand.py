from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from logistics.apps.malawi.handlers.abstract.stockreport import StockReportBaseHandler
from logistics.apps.malawi.shortcuts import send_soh_responses

class StockOnHandReportHandler(StockReportBaseHandler):
    """
    A stock on hand report.
    """

    keyword = "soh"

    def help(self):
        self.respond(config.Messages.SOH_HELP_MESSAGE)
    
    def get_report_type(self):
        return Reports.SOH
      
    def send_responses(self, stock_report):
        send_soh_responses(self.msg, stock_report, self.requests)
        