from logistics.apps.logistics.models import ProductReportsHelper, ContactRole
from logistics.apps.logistics.util import config
from rapidsms.models import Contact


def create_stock_report(report_type, supply_point, text, logger_msg=None):
    """
    Gets a stock report helper object parses it, and saves it.
    """
    stock_report = ProductReportsHelper(supply_point, 
                                        report_type,  
                                        logger_msg)
    stock_report.parse(text)
    stock_report.save()
    return stock_report

def send_soh_responses(msg, stock_report, requests):
    if stock_report.errors:
        # TODO: respond better.
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        supervisors = Contact.objects.filter(role=ContactRole.objects.get(code=config.Roles.IN_CHARGE), 
                                             supply_point=msg.logistics_contact.supply_point.supplied_by)
        for super in supervisors:
            super.message(config.Messages.SUPERVISOR_SOH_NOTIFICATION, 
                          hsa=msg.logistics_contact.name,
                          products=", ".join(req.sms_format() for req in requests),
                          hsa_id=msg.logistics_contact.supply_point.code)
        if supervisors.count() > 0:
            msg.respond(config.Messages.SOH_ORDER_CONFIRM,
                        contact=msg.logistics_contact.name)
        else:
            msg.respond(config.Messages.NO_IN_CHARGE,
                            supply_point=msg.logistics_contact.supply_point.supplied_by.name)
        
    
def send_emergency_responses(msg, stock_report, requests):
    if stock_report.errors:
        # TODO: respond better.
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        supervisors = Contact.objects.filter(role=ContactRole.objects.get(code=config.Roles.IN_CHARGE), 
                                             supply_point=msg.logistics_contact.supply_point.supplied_by)
        
        emergency_products = [req for req in requests if req.is_emergency == True]
        emergency_product_string = ", ".join(req.sms_format() for req in emergency_products) if emergency_products else "none"
        normal_products = [req for req in requests if req.is_emergency == False]
        for supervisor in supervisors:
            if normal_products:
                supervisor.message(config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION, 
                                   hsa=msg.logistics_contact.name,
                                   emergency_products=emergency_product_string,
                                   normal_products=", ".join(req.sms_format() for req in normal_products),
                                   hsa_id=msg.logistics_contact.supply_point.code)
            else:
                supervisor.message(config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION_NO_ADDITIONAL, 
                                   hsa=msg.logistics_contact.name,
                                   emergency_products=emergency_product_string,
                                   hsa_id=msg.logistics_contact.supply_point.code)
        if supervisors.count() > 0:
            msg.respond(config.Messages.SOH_ORDER_CONFIRM,
                        contact=msg.logistics_contact.name)
        else:
            # TODO: this message should probably be cleaned up
            msg.respond(config.Messages.NO_IN_CHARGE,
                        supply_point=msg.logistics_contact.supply_point.supplied_by.name)
    
        
    