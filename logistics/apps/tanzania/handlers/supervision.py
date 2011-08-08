from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
import re
from logistics.apps.ilsgateway.models import ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType
import datetime
from logistics.apps.logistics.util import config
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes
from logistics.apps.logistics.decorators import logistics_contact_required
        
class Supervision(KeywordHandler):
    """
    Supervision handler for responses to supervision inquiries
    """

    keyword = "supervision|usimamizi"    

    def help(self):        
        self.respond(_(config.Messages.SUPERVISION_HELP))
    
    @logistics_contact_required()
    def handle(self, text):
        sub_command = text.strip().lower()
        if re.match("hap", sub_command) or re.match("no", sub_command):
            SupplyPointStatus.objects.create\
                (status_type=SupplyPointStatusTypes.SUPERVISION_NOT_RECEIVED_FACILITY,
                 supply_point=self.msg.logistics_contact.supply_point)
            self.respond(_(config.Messages.SUPERVISION_CONFIRM_NO))
        elif re.match("ndi", sub_command) or re.match("yes", sub_command):
            SupplyPointStatus.objects.create\
                (status_type=SupplyPointStatusTypes.SUPERVISION_RECEIVED_FACILITY,
                 supply_point=self.msg.logistics_contact.supply_point)
            self.respond(_(config.Messages.SUPERVISION_CONFIRM_YES))
        else:
            self.help()
