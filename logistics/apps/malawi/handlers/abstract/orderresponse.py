from django.utils.translation import ugettext as _
from logistics.apps.logistics.models import SupplyPoint
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.malawi.const import Messages, Operations
from logistics.apps.malawi.roles import user_can_do
from logistics.apps.malawi import util


class OrderResponseBaseHandler(KeywordHandler):
    hsa = None
    
    def handle_preconditions(self, text):
        """
        Check some precondidtions, based on shared assumptions of these handlers.
        Return true if there is a precondition that wasn't met. If all preconditions
        are met, the variables for facility and name will be set.
        
        This method will manage some replies as well.
        """
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(Messages.REGISTRATION_REQUIRED_MESSAGE)
        # at some point we may want more granular permissions for these
        # operations, but for now we just share the one
        elif not user_can_do(self.msg.logistics_contact, Operations.FILL_ORDER):
            self.respond(Messages.UNSUPPORTED_OPERATION)
        
        else:
            words = text.split(" ")
            hsa_id = words[0]
            self.hsa = util.get_hsa(hsa_id)
            if self.hsa is None:
                self.respond(Messages.UNKNOWN_HSA, hsa_id=hsa_id)
                
            