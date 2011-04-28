from datetime import datetime
from logistics.apps.logistics.models import StockRequest, ContactRole
from logistics.apps.malawi.const import Messages, Roles
from logistics.apps.malawi.handlers.abstract.orderresponse import OrderResponseBaseHandler
from rapidsms.models import Contact

class OrderStockoutHandler(OrderResponseBaseHandler):
    """
    When a supply has been ordered and can't be filled, it is marked 
    out of stock with this handler.
    """

    keyword = "os|so|out"

    def help(self):
        self.respond(Messages.STOCKOUT_HELP)
        
    def handle_custom(self, text):
        now = datetime.utcnow()
        
        # Currently we just mark these stock requests stocked out.
        pending_reqs = StockRequest.pending_requests().filter(supply_point=self.hsa.supply_point)
        for req in pending_reqs:
            req.mark_stockout(self.msg.logistics_contact, now)
        
        products = ", ".join(req.sms_format() for req in pending_reqs)
        self.respond(Messages.STOCKOUT_RESPONSE, reporter=self.msg.logistics_contact.name,
                     products=products)
        self.hsa.message(Messages.STOCKOUT_NOTICE, hsa=self.hsa.name)
        supplier = self.msg.logistics_contact.supply_point.supplied_by
        if supplier is not None:
            supervisors = Contact.objects.filter(supply_point=supplier, 
                                                 role__in=[ContactRole.objects.get(code=Roles.DISTRICT_PHARMACIST),
                                                           ContactRole.objects.get(code=Roles.IMCI_COORDINATOR)])
            # note that if there are no supervisors registered, this will silently
            # not send notifications 
            for super in supervisors:
                super.message(Messages.SUPERVISOR_STOCKOUT_NOTIFICATION, 
                              contact=self.msg.logistics_contact.name,
                              supply_point=self.msg.logistics_contact.supply_point.name,
                              products=products)
            