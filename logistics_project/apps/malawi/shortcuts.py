from logistics.models import StockRequest, StockRequestStatus
from logistics.util import config, ussd_msg_response
from logistics_project.apps.malawi.util import get_supervisors
from rapidsms.messages.outgoing import OutgoingMessage


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
    
def _respond_empty(msg, contact, stock_report, supervisors, supply_point_name):
    for super in supervisors:
        super.message(config.Messages.SUPERVISOR_SOH_NOTIFICATION_NOTHING_TO_DO,
                      supply_point=supply_point_name)
    msg.respond(config.Messages.SOH_ORDER_CONFIRM_NOTHING_TO_DO,
                products=" ".join(stock_report.reported_products()).strip(),
                contact=supply_point_name)

def send_soh_responses(msg, contact, stock_report, requests, base_level=config.BaseLevel.HSA):
    if stock_report.errors:
        # TODO: respond better.
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        base_level_is_hsa = (base_level == config.BaseLevel.HSA)
        supply_point_name = contact.name if base_level_is_hsa else contact.supply_point.name
        supervisors = get_supervisors(contact.supply_point.supplied_by)

        if not requests:
            _respond_empty(msg, contact, stock_report, supervisors, supply_point_name)
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
                    if base_level_is_hsa:
                        super.message(config.Messages.SUPERVISOR_HSA_LEVEL_SOH_NOTIFICATION_WITH_STOCKOUTS,
                                      hsa=supply_point_name,
                                      products=orders,
                                      stockedout_products=stocked_out,
                                      hsa_id=contact.supply_point.code)
                    else:
                        super.message(config.Messages.SUPERVISOR_FACILITY_LEVEL_SOH_NOTIFICATION_WITH_STOCKOUTS,
                                      supply_point=supply_point_name,
                                      products=orders,
                                      stockedout_products=stocked_out,
                                      supply_point_code=contact.supply_point.code)

                if base_level_is_hsa:
                    msg.respond(config.Messages.SOH_HSA_LEVEL_ORDER_STOCKOUT_CONFIRM, products=stocked_out)
                else:
                    msg.respond(config.Messages.SOH_FACILITY_LEVEL_ORDER_STOCKOUT_CONFIRM, products=stocked_out)

            else:
                for super in supervisors:
                    if base_level_is_hsa:
                        super.message(config.Messages.SUPERVISOR_HSA_LEVEL_SOH_NOTIFICATION,
                                      hsa=supply_point_name,
                                      products=orders,
                                      hsa_id=contact.supply_point.code)
                    else:
                        super.message(config.Messages.SUPERVISOR_FACILITY_LEVEL_SOH_NOTIFICATION,
                                      supply_point=supply_point_name,
                                      products=orders,
                                      supply_point_code=contact.supply_point.code)

                if base_level_is_hsa:
                    response_message = config.Messages.SOH_HSA_LEVEL_ORDER_CONFIRM
                else:
                    response_message = config.Messages.SOH_FACILITY_LEVEL_ORDER_CONFIRM

                ussd_msg_response(
                    msg,
                    response_message,
                    products=" ".join(stock_report.reported_products()).strip()
                )


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
            ussd_msg_response(
                msg,
                config.Messages.EMERGENCY_SOH,
                products=" ".join(stock_report.reported_products()).strip()
            )
        else:
            # TODO: this message should probably be cleaned up
            msg.respond(config.Messages.NO_IN_CHARGE,
                        supply_point=contact.supply_point.supplied_by.name)
