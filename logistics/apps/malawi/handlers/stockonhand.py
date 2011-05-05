from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from logistics.apps.malawi.handlers.abstract.stockreport import StockReportBaseHandler

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
        if stock_report.errors:
            # TODO: respond better.
            self.respond(config.Messages.GENERIC_ERROR)
        else:
            try:
                supervisor = Contact.objects.get(role=ContactRole.objects.get(code=config.Roles.IN_CHARGE), 
                                                 supply_point=self.msg.logistics_contact.supply_point.supplied_by)
                supervisor.message(config.Messages.SUPERVISOR_SOH_NOTIFICATION, 
                                   hsa=self.msg.logistics_contact.name,
                                   products=", ".join(req.sms_format() for req in self.requests),
                                   hsa_id=self.msg.logistics_contact.supply_point.code)
                self.respond(config.Messages.SOH_ORDER_CONFIRM,
                                contact=self.msg.logistics_contact.name)
            
            except Contact.DoesNotExist:
                self.respond(config.Messages.NO_IN_CHARGE,
                                supply_point=self.msg.logistics_contact.supply_point.supplied_by.name)
            
        