from __future__ import unicode_literals
from logistics.const import Reports
from logistics.util import config
from logistics_project.apps.malawi.handlers.abstract.stockreport import StockReportBaseHandler
from logistics_project.apps.malawi.shortcuts import send_soh_responses

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
        send_soh_responses(self.msg, self.msg.logistics_contact, stock_report, self.requests, base_level=self.base_level)
