from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.apps.logistics.util import config
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from logistics.apps.logistics.decorators import logistics_contact_required

class NotSubmitted(KeywordHandler):
    
    keyword = "sijatuma"

    def help(self):
        self.handle(text="")
        
    @logistics_contact_required()
    def handle(self, text):
        SupplyPointStatus.objects.create(status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                         status_value=SupplyPointStatusValues.NOT_SUBMITTED,
                                         supply_point=self.msg.logistics_contact.supply_point)
        self.respond(_(config.Messages.NOT_SUBMITTED_CONFIRM))