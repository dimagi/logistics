from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
import datetime
import re
from django.utils.translation import ugettext_noop as _
from logistics.util import config
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from logistics.decorators import logistics_contact_required
        
class Not(KeywordHandler,TaggingHandler):
    """
    Simple "not"
    """
    
    # this is rather ugly, but serves as the english language translation of 
    # multiple handlers, because the english keyword is actually two words
    # even though the swahili keyword is only a single word.
    keyword = "not|no|hapana"    

    def help(self):
        self.respond(_(config.Messages.NOT_HELP))

    @logistics_contact_required()
    def handle(self, text):
        if re.match("del", text.strip().lower() ):
            SupplyPointStatus.objects.create\
                (status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                 status_value=SupplyPointStatusValues.NOT_RECEIVED,
                 supply_point=self.msg.logistics_contact.supply_point,
                 status_date=self.msg.timestamp)
            self.respond(_(config.Messages.NOT_DELIVERED_CONFIRM))
        elif re.match("sub", text.strip().lower() ):
            SupplyPointStatus.objects.create\
                (status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                 status_value=SupplyPointStatusValues.NOT_SUBMITTED,
                 supply_point=self.msg.logistics_contact.supply_point,
                 status_date=self.msg.timestamp)
            self.respond(_(config.Messages.NOT_SUBMITTED_CONFIRM))
        else:
            self.add_tag("Error")
            self.help()
