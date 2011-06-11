from logistics.apps.logistics.models import ProductReportsHelper, ContactRole,\
    StockRequest, StockRequestStatus, ProductStock
from logistics.apps.logistics.util import config
from rapidsms.models import Contact
from logistics.apps.malawi.util import get_supervisors


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

def send_transfer_responses(msg, stock_report, transfers, giver, to):
    
    if stock_report.errors:
        # TODO: respond better.
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        msg.respond(config.Messages.TRANSFER_RESPONSE, 
                    reporter=msg.logistics_contact.name,
                    giver=giver.name,
                    receiver=to.name,
                    products=stock_report.all())
        to.message(config.Messages.TRANSFER_CONFIRM, 
                   giver=giver.name,
                   products=stock_report.all())
    
def _respond_empty(msg, contact, stock_report, supervisors):
    for super in supervisors:
        super.message(config.Messages.SUPERVISOR_SOH_NOTIFICATION_NOTHING_TO_DO,
                      hsa=contact.name)
    msg.respond(config.Messages.SOH_ORDER_CONFIRM_NOTHING_TO_DO,
                products=" ".join(stock_report.reported_products()).strip(),
                contact=contact.name)

def send_soh_responses(msg, contact, stock_report, requests):
    if stock_report.errors:
        # TODO: respond better.
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        supervisors = get_supervisors(contact.supply_point.supplied_by)
        
        if not requests:
            _respond_empty(msg, contact, stock_report, supervisors)
        else:
            if supervisors.count() == 0:
                msg.respond(config.Messages.NO_IN_CHARGE,
                            supply_point=contact.supply_point.supplied_by.name)
                return

            if stock_report.stockouts():
                for super in supervisors:
                    super.message(config.Messages.SOH_ORDER_STOCKOUT_SUPERVISOR,
                                contact=contact.name,
                                products=stock_report.stockouts())
                msg.respond(config.Messages.SOH_ORDER_STOCKOUT,
                            contact = contact.name,
                            products=stock_report.stockouts())
            else:
                for super in supervisors:
                    super.message(config.Messages.SUPERVISOR_SOH_NOTIFICATION,
                                  hsa=contact.name,
                                  products=", ".join(req.sms_format() for req in \
                                                     StockRequest.objects.filter(\
                                                        supply_point=stock_report.supply_point,
                                                        status=StockRequestStatus.REQUESTED)),
                                  hsa_id=contact.supply_point.code)
                msg.respond(config.Messages.SOH_ORDER_CONFIRM,
                            products=" ".join(stock_report.reported_products()).strip())


def send_emergency_responses(msg, contact, stock_report, requests):
    if stock_report.errors:
        # TODO: respond better.
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        supervisors = get_supervisors(contact.supply_point.supplied_by)
        
        emergency_products = [req for req in requests if req.is_emergency == True]
        emergency_product_string = ", ".join(req.sms_format() for req in emergency_products) if emergency_products else "none"
        normal_products = [req for req in requests if req.is_emergency == False]
        for supervisor in supervisors:
            if normal_products:
                supervisor.message(config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION, 
                                   hsa=contact.name,
                                   emergency_products=emergency_product_string,
                                   normal_products=", ".join(req.sms_format() for req in normal_products),
                                   hsa_id=contact.supply_point.code)
            else:
                supervisor.message(config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION_NO_ADDITIONAL, 
                                   hsa=contact.name,
                                   emergency_products=emergency_product_string,
                                   hsa_id=contact.supply_point.code)
        if supervisors.count() > 0:
            msg.respond(config.Messages.EMERGENCY_SOH,
                        products=" ".join(stock_report.reported_products()).strip())
        else:
            # TODO: this message should probably be cleaned up
            msg.respond(config.Messages.NO_IN_CHARGE,
                        supply_point=contact.supply_point.supplied_by.name)
    
        
    