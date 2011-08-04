from django.db import transaction
from logistics.apps.logistics.util import config
from logistics.apps.logistics.decorators import logistics_contact_and_permission_required
from logistics.apps.malawi import util
from logistics.apps.malawi.handlers.abstract.base import RecordResponseHandler


class OrderResponseBaseHandler(RecordResponseHandler):
    hsa = None
    
    def handle_custom(self, text):
        raise NotImplemented("This method must be overridden")
    
    @transaction.commit_on_success
    @logistics_contact_and_permission_required(config.Operations.FILL_ORDER)
    def handle(self, text):
        """
        Check some preconditions, based on shared assumptions of these handlers.
        
        Calls handle custom if things go well, otherwise responds directly and 
        doesn't call the subclass method.
        """
    
        words = text.split(" ")
        hsa_id = words[0]
        self.hsa = util.get_hsa(hsa_id)
        if self.hsa is None:
            self.respond(config.Messages.UNKNOWN_HSA, hsa_id=hsa_id)
        else:
            self.handle_custom(text)
            
