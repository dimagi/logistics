from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from config import Messages
from logistics.apps.malawi.handlers.abstract.stockreport import StockReportBaseHandler

class EmergencyReportHandler(StockReportBaseHandler):
    """
    A lot like a SOH report, except only used in emergency situations.
    """

    keyword = "eo|emergency|urgent"

    def help(self):
        self.respond(Messages.EMERGENCY_HELP)
    
    def get_report_type(self):
        return Reports.EMERGENCY_SOH
      
    def send_responses(self, stock_report):
        if stock_report.errors:
            # TODO: respond better.
            self.respond(Messages.GENERIC_ERROR)
        else:
            try:
                supervisor = Contact.objects.get(role=ContactRole.objects.get(code=config.Roles.IN_CHARGE), 
                                                 supply_point=self.msg.logistics_contact.supply_point.supplied_by)
                
                supervisor.message(Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION, 
                                   hsa=self.msg.logistics_contact.name,
                                   emergency_products=", ".join(req.sms_format() for req in self.requests if req.is_emergency),
                                   normal_products=", ".join(req.sms_format() for req in self.requests if not req.is_emergency),
                                   hsa_id=self.msg.logistics_contact.supply_point.code)
                self.respond(Messages.SOH_ORDER_CONFIRM,
                             contact=self.msg.logistics_contact.name)
            
            except Contact.DoesNotExist:
                self.respond(Messages.NO_IN_CHARGE,
                             supply_point=self.msg.logistics_contact.supply_point.supplied_by.name)
            
        