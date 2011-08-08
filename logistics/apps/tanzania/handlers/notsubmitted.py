from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.apps.logistics.util import config
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes
from logistics.apps.logistics.decorators import logistics_contact_required

class NotSubmitted(KeywordHandler):
    
    keyword = "sijatuma"

    def help(self):
        self.handle(text="")
        
    @logistics_contact_required()
    def handle(self, text):
        SupplyPointStatus.objects.create(status_type=SupplyPointStatusTypes.R_AND_R_SUBMITTED_FACILITY_TO_DISTRICT,
                                         supply_point=self.msg.logistics_contact.supply_point)
        self.respond(_(config.Messages.NOT_SUBMITTED_CONFIRM))