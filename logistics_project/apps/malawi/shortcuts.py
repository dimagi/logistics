from logistics.models import StockRequest, StockRequestStatus
from logistics.util import config
from logistics_project.apps.malawi.util import get_supervisors


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

            
            orders = ", ".join(req.sms_format() for req in \
                               StockRequest.objects.filter\
                                    (supply_point=stock_report.supply_point,
                                     status=StockRequestStatus.REQUESTED))
                
            if stock_report.stockouts():
                stocked_out = stock_report.stockouts()
                for super in supervisors:
                    super.message(config.Messages.SUPERVISOR_SOH_NOTIFICATION_WITH_STOCKOUTS,
                                  hsa=contact.name,
                                  products=orders,
                                  stockedout_products=stocked_out,
                                  hsa_id=contact.supply_point.code)
                msg.respond(config.Messages.SOH_ORDER_STOCKOUT_CONFIRM,
                            products=stocked_out)

            else:
                for super in supervisors:
                    super.message(config.Messages.SUPERVISOR_SOH_NOTIFICATION,
                                  hsa=contact.name,
                                  products=orders,
                                  hsa_id=contact.supply_point.code)

                msg.respond(config.Messages.SOH_ORDER_CONFIRM,
                            products=" ".join(stock_report.reported_products()).strip())

def send_emergency_responses(msg, contact, stock_report, requests):
    if stock_report.errors:
        # TODO: respond better.
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        supervisors = get_supervisors(contact.supply_point.supplied_by)
        stockouts = [req for req in requests if req.balance == 0]
        emergency_products = [req for req in requests if req.is_emergency == True]
        emergency_product_string = ", ".join(req.sms_format() for req in emergency_products) if emergency_products else "none"
        stockout_string = ", ".join(req.sms_format() for req in stockouts) if stockouts else "none"
        if stockouts:
            normal_products = [req for req in requests if req.balance > 0]
        else:
            normal_products = [req for req in requests if req.is_emergency == False]
        for supervisor in supervisors:
            if stockouts:
                if normal_products:
                    supervisor.message(config.Messages.EMERGENCY_STOCKOUT,
                                       hsa=contact.name,
                                       stockouts=stockout_string,
                                       normal_products=", ".join(req.sms_format() for req in normal_products),
                                       hsa_id=contact.supply_point.code)
                else:
                    supervisor.message(config.Messages.EMERGENCY_STOCKOUT_NO_ADDITIONAL,
                                       hsa=contact.name,
                                       stockouts=stockout_string,
                                       hsa_id=contact.supply_point.code)
            else:
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
    
        
    