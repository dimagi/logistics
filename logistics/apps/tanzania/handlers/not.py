from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
import datetime
import re
from django.utils.translation import ugettext_noop as _
from logistics.apps.logistics.util import config
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes
        
class Not(KeywordHandler):
    """
    Simple "not"
    """
    
    # this is rather ugly, but serves as the english language translation of 
    # multiple handlers, because the english keyword is actually two words
    # even though the swahili keyword is only a single word.
    keyword = "not|no|hapana"    

    def help(self):
        self.respond(_(config.Messages.NOT_HELP))

    def handle(self, text):
        if re.match("del", text.strip().lower() ):
            SupplyPointStatus.objects.create\
                (status_type=SupplyPointStatusTypes.DELIVERY_NOT_RECEIVED_FACILITY,
                 supply_point=self.msg.logistics_contact.supply_point)
            self.respond(_(config.Messages.NOT_DELIVERED_CONFIRM))
        elif re.match("sub", text.strip().lower() ):
            SupplyPointStatus.objects.create\
                (status_type=SupplyPointStatusTypes.R_AND_R_SUBMITTED_FACILITY_TO_DISTRICT,
                 supply_point=self.msg.logistics_contact.supply_point)
            self.respond(_(config.Messages.NOT_SUBMITTED_CONFIRM))
        else:
            self.help()