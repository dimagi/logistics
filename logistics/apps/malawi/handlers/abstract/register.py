from django.utils.translation import ugettext as _
from logistics.apps.logistics.models import SupplyPoint
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.malawi.handlers.abstract.base import RecordResponseHandler

class RegistrationBaseHandler(RecordResponseHandler):
    supply_point = None
    contact_name = ""
    extra = None
    
    def handle_preconditions(self, text):
        """
        Check some precondidtions, based on shared assumptions of these handlers.
        Return true if there is a precondition that wasn't met. If all preconditions
        are met, the variables for facility and name will be set.
        
        This method will manage some replies as well.
        """
        if hasattr(self.msg,'logistics_contact') and self.msg.logistics_contact.is_active:
            self.respond("You are already registered. To change your information you must first text LEAVE")
        
        words = text.split()
        if len(words) < 3:
            self.help()
        else:
            self.contact_name = " ".join(words[:-2])
            self.extra =   words[-2]
            code = words[-1]
            try:
                self.supply_point = SupplyPoint.objects.get(code__iexact=code)
            except SupplyPoint.DoesNotExist:
                self.respond(_("Sorry, can't find the location with CODE %(code)s"), code=code )

        return self.responded
        
