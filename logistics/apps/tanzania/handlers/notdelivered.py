from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.apps.logistics.util import config
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes
from logistics.apps.logistics.decorators import logistics_contact_required

class NotDelivered(KeywordHandler):
    
    keyword = "sijapokea"

    def help(self):
        self.handle(text="")
        
    @logistics_contact_required()
    def handle(self, text):
        SupplyPointStatus.objects.create(status_type=SupplyPointStatusTypes.DELIVERY_NOT_RECEIVED_FACILITY,
                                         supply_point=self.msg.logistics_contact.supply_point)
        self.respond(_(config.Messages.NOT_DELIVERED_CONFIRM))