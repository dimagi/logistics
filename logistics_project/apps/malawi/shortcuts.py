from logistics.models import StockRequest, StockRequestStatus, format_product_string
from logistics.util import config, ussd_msg_response
from logistics_project.apps.malawi.util import get_supervisors, swallow_errors
from rapidsms.messages.outgoing import OutgoingMessage


def send_transfer_responses(msg, stock_report, giver, receiver_sp, receiver_contacts, base_level=config.BaseLevel.HSA):
    
    if stock_report.errors:
        # TODO: respond better.
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        if base_level == config.BaseLevel.HSA:
            msg.respond(config.Messages.TRANSFER_RESPONSE,
                        reporter=msg.logistics_contact.name,
                        giver=giver.name,
                        receiver=receiver_contacts[0].name,
                        products=stock_report.all())
        else:
            msg.respond(config.Messages.TRANSFER_RESPONSE,
                        reporter=msg.logistics_contact.name,
                        giver=giver.supply_point.name,
                        receiver=receiver_sp.name,
                        products=stock_report.all())

        for contact in receiver_contacts:
            if base_level == config.BaseLevel.HSA:
                contact.message(config.Messages.TRANSFER_CONFIRM,
                                giver=giver.name,
                                products=stock_report.all())
            else:
                contact.message(config.Messages.TRANSFER_CONFIRM,
                                giver=giver.supply_point.name,
                                products=stock_report.all())


def _respond_empty(msg, contact, stock_report, supervisors, supply_point_name):
    for super in supervisors:
        with swallow_errors():
            super.message(config.Messages.SUPERVISOR_SOH_NOTIFICATION_NOTHING_TO_DO,
                          supply_point=supply_point_name)
    msg.respond(config.Messages.SOH_ORDER_CONFIRM_NOTHING_TO_DO,
                products=" ".join(stock_report.reported_products()).strip(),
                contact=supply_point_name)

def send_soh_responses(msg, contact, stock_report, requests, base_level=config.BaseLevel.HSA):
    if stock_report.errors:
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

            raw_orders = [
                req.sms_format() for req in
                StockRequest.objects.filter(supply_point=stock_report.supply_point,
                                            status=StockRequestStatus.REQUESTED)
            ]
            orders = format_product_string(raw_orders, delimiter=", ")

            if stock_report.stockouts():
                stocked_out = stock_report.stockouts()
                for super in supervisors:
                    with swallow_errors():
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
                    with swallow_errors():
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


def send_emergency_responses(msg, contact, stock_report, requests, base_level=config.BaseLevel.HSA):
    if stock_report.errors:
        msg.respond(config.Messages.GENERIC_ERROR)
    else:
        base_level_is_hsa = (base_level == config.BaseLevel.HSA)
        supply_point_name = contact.name if base_level_is_hsa else contact.supply_point.name
        supervisors = get_supervisors(contact.supply_point.supplied_by)
        stockouts = [req for req in requests if req.balance == 0]
        emergency_products = [req for req in requests if req.is_emergency]
        emergency_product_string = format_product_string(
            [req.sms_format() for req in emergency_products], delimiter=', '
        ) if emergency_products else "none"
        stockout_string = format_product_string(
            [req.sms_format() for req in stockouts], delimiter=', '
        ) if stockouts else "none"

        if stockouts:
            normal_products = [req for req in requests if req.balance > 0]
        else:
            normal_products = [req for req in requests if req.is_emergency]
        for supervisor in supervisors:
            with swallow_errors():
                if stockouts:
                    if normal_products:
                        supervisor.message(config.Messages.EMERGENCY_STOCKOUT,
                                           supply_point=supply_point_name,
                                           stockouts=stockout_string,
                                           normal_products=", ".join(req.sms_format() for req in normal_products),
                                           supply_point_code=contact.supply_point.code)
                    else:
                        supervisor.message(config.Messages.EMERGENCY_STOCKOUT_NO_ADDITIONAL,
                                           supply_point=supply_point_name,
                                           stockouts=stockout_string,
                                           supply_point_code=contact.supply_point.code)
                else:
                    if normal_products:
                        supervisor.message(config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION,
                                           supply_point=supply_point_name,
                                           emergency_products=emergency_product_string,
                                           normal_products=", ".join(req.sms_format() for req in normal_products),
                                           supply_point_code=contact.supply_point.code)
                    else:
                        supervisor.message(config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION_NO_ADDITIONAL,
                                           supply_point=supply_point_name,
                                           emergency_products=emergency_product_string,
                                           supply_point_code=contact.supply_point.code)
        if supervisors.count() > 0:
            ussd_msg_response(
                msg,
                config.Messages.HSA_LEVEL_EMERGENCY_SOH if base_level_is_hsa else config.Messages.FACILITY_LEVEL_EMERGENCY_SOH,
                products=format_product_string(stock_report.reported_products()),
            )
        else:
            # TODO: this message should probably be cleaned up
            msg.respond(config.Messages.NO_IN_CHARGE,
                        supply_point=contact.supply_point.supplied_by.name)
