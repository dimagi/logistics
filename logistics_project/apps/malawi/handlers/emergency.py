from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from logistics.apps.malawi.handlers.abstract.stockreport import StockReportBaseHandler
from logistics.apps.malawi.shortcuts import send_emergency_responses

class EmergencyReportHandler(StockReportBaseHandler):
    """
    A lot like a SOH report, except only used in emergency situations.
    """

    keyword = "eo|emergency|urgent"

    def help(self):
        self.respond(config.Messages.EMERGENCY_HELP)
    
    def get_report_type(self):
        return Reports.EMERGENCY_SOH
      
    def send_responses(self, stock_report):
        send_emergency_responses(self.msg, self.msg.logistics_contact, stock_report, self.requests)