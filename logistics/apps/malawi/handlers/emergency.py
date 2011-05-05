from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from logistics.apps.malawi.handlers.abstract.stockreport import StockReportBaseHandler

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
        if stock_report.errors:
            # TODO: respond better.
            self.respond(config.Messages.GENERIC_ERROR)
        else:
            try:
                supervisor = Contact.objects.get(role=ContactRole.objects.get(code=config.Roles.IN_CHARGE), 
                                                 supply_point=self.msg.logistics_contact.supply_point.supplied_by)
                
                emergency_products = [req for req in self.requests if req.is_emergency == True]
                emergency_product_string = ", ".join(req.sms_format() for req in emergency_products) if emergency_products else "none"
                normal_products = [req for req in self.requests if req.is_emergency == False]
                if normal_products:
                    supervisor.message(config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION, 
                                       hsa=self.msg.logistics_contact.name,
                                       emergency_products=emergency_product_string,
                                       normal_products=", ".join(req.sms_format() for req in normal_products),
                                       hsa_id=self.msg.logistics_contact.supply_point.code)
                else:
                    supervisor.message(config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION_NO_ADDITIONAL, 
                                       hsa=self.msg.logistics_contact.name,
                                       emergency_products=emergency_product_string,
                                       hsa_id=self.msg.logistics_contact.supply_point.code)
                self.respond(config.Messages.SOH_ORDER_CONFIRM,
                             contact=self.msg.logistics_contact.name)
            
            except Contact.DoesNotExist:
                self.respond(config.Messages.NO_IN_CHARGE,
                             supply_point=self.msg.logistics_contact.supply_point.supplied_by.name)
            
        