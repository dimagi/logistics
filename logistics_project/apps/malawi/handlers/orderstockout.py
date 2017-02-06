from datetime import datetime
from logistics.decorators import logistics_contact_and_permission_required
from logistics.models import StockRequest, ContactRole,\
    ProductStock
from logistics.util import config
from logistics_project.apps.malawi.handlers.abstract.orderresponse import OrderResponseBaseHandler
from logistics_project.decorators import validate_base_level_from_supervisor
from rapidsms.models import Contact


class OrderStockoutHandler(OrderResponseBaseHandler):
    """
    When a supply has been ordered and can't be filled, it is marked 
    out of stock with this handler.
    """

    keyword = "os|so|out"

    @logistics_contact_and_permission_required(config.Operations.FILL_ORDER)
    @validate_base_level_from_supervisor([config.BaseLevel.HSA, config.BaseLevel.FACILITY])
    def help(self):
        if self.base_level_is_hsa:
            self.respond(config.Messages.HSA_LEVEL_STOCKOUT_HELP)
        else:
            self.respond(config.Messages.FACILITY_LEVEL_STOCKOUT_HELP)

    def handle_custom(self, text):
        now = datetime.utcnow()
        
        # Currently we just mark these stock requests stocked out.
        # Note that this has a different meaning for emergency orders
        # in which case we only confirm the emergency products.
        # However in the interest of simplicity we won't worry about that (yet?).
        pending_reqs = StockRequest.pending_requests().filter(supply_point=self.supply_point)
        for req in pending_reqs:
            req.mark_stockout(self.msg.logistics_contact, now)
        
        # if there were any emergency orders, only report those as stockouts
        # this is pretty confusing/hacky
        emergencies = pending_reqs.filter(is_emergency=True)
        stockouts = pending_reqs.filter(balance=0)
        if stockouts.count() > 0:
            reqs = stockouts
        elif emergencies.count() > 0:
            reqs = emergencies
        else:
            reqs = pending_reqs

        def _message_supervisors(message):
            supplier = self.msg.logistics_contact.supply_point.supplied_by
            if supplier is not None:
                if self.base_level_is_hsa:
                    supervisor_roles = [config.Roles.DISTRICT_PHARMACIST, config.Roles.IMCI_COORDINATOR]
                else:
                    supervisor_roles = [config.Roles.REGIONAL_EPI_COORDINATOR]
                supervisors = Contact.objects.filter(is_active=True,
                                                     supply_point__location=supplier.location,
                                                     role__code__in=supervisor_roles)
                # note that if there are no supervisors registered, this will silently
                # not send notifications
                for super in supervisors:
                    super.message(message,
                                  contact=self.msg.logistics_contact.name,
                                  supply_point=self.msg.logistics_contact.supply_point.name,
                                  products=", ".join(req.product.sms_code for req in reqs))

        product_string = ", ".join(req.product.sms_code for req in reqs)
        if emergencies.count() > 0:
            # Unable to resupply stocked out/emergency products.
            self.respond(
                config.Messages.HSA_LEVEL_OS_EO_RESPONSE if self.base_level_is_hsa else config.Messages.FACILITY_LEVEL_OS_EO_RESPONSE,
                products=product_string
            )
            for contact in self.contacts:
                if self.base_level_is_hsa:
                    contact.message(config.Messages.UNABLE_RESTOCK_EO_HSA_NOTIFICATION, hsa=contact.name, products=product_string)
                else:
                    contact.message(config.Messages.UNABLE_RESTOCK_EO_FACILITY_NOTIFICATION, supply_point=self.supply_point.name, products=product_string)

            if stockouts.count() > 0:
                _message_supervisors(
                    config.Messages.UNABLE_RESTOCK_STOCKOUT_DISTRICT_ESCALATION if self.base_level_is_hsa
                    else config.Messages.UNABLE_RESTOCK_STOCKOUT_ZONE_ESCALATION
                )
            else:
                _message_supervisors(
                    config.Messages.UNABLE_RESTOCK_EO_DISTRICT_ESCALATION if self.base_level_is_hsa
                    else config.Messages.UNABLE_RESTOCK_EO_ZONE_ESCALATION
                )
        else:
            self.respond(
                config.Messages.HSA_LEVEL_OS_EO_RESPONSE if self.base_level_is_hsa else config.Messages.FACILITY_LEVEL_OS_EO_RESPONSE,
                products=product_string
            )
            for contact in self.contacts:
                if self.base_level_is_hsa:
                    contact.message(config.Messages.UNABLE_RESTOCK_HSA_NOTIFICATION, hsa=contact.name)
                else:
                    contact.message(config.Messages.UNABLE_RESTOCK_FACILITY_NOTIFICATION, supply_point=self.supply_point.name)

            _message_supervisors(
                config.Messages.UNABLE_RESTOCK_NORMAL_DISTRICT_ESCALATION if self.base_level_is_hsa
                else config.Messages.UNABLE_RESTOCK_NORMAL_ZONE_ESCALATION
            )

            
        # this is pretty hacky, but set the SoH to 0 for the stocked out products
        # so that they show properly in things like alerts
        for req in reqs:
            self.msg.logistics_contact.supply_point.update_stock(req.product, 0)

