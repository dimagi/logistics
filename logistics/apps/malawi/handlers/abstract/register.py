from django.utils.translation import ugettext as _
from logistics.apps.logistics.models import SupplyPoint
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

# Rather than hack rapidsms to understand the notion of an abstract handler
# we use this 'abstract' class as a real handler that others can override.
# I would prefer this live in the same module as the subclasses, but 
# unfortunately rapidsms also doesn't like that. 

class RegistrationBaseHandler(KeywordHandler):
    help_message = "You shouldn't be seeing this message. Something is very wrong."
    _responded = False
    supply_point = None
    contact_name = ""
    extra = None
    
    def help(self):
        self.respond(_(self.help_message))
    
    def respond(self, template, **kwargs):
        super(RegistrationBaseHandler, self).respond(template, **kwargs)
        self._responded = True
    
    def handle_preconditions(self, text):
        """
        Check some precondidtions, based on shared assumptions of these handlers.
        Return true if there is a precondition that wasn't met. If all preconditions
        are met, the variables for facility and name will be set.
        
        This method will manage replies as well.
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

        return self._responded
        
