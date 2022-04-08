from __future__ import unicode_literals
from django.utils.translation import gettext as _
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.handlers.abstract.base import RecordResponseHandler
from logistics.util import config


class RegistrationBaseHandler(RecordResponseHandler):
    supply_point = None
    contact_name = ""
    extra = None
    
    def handle_preconditions(self, text):
        """
        Check some preconditions, based on shared assumptions of these handlers.
        Return true if there is a precondition that wasn't met. If all preconditions
        are met, the variables for facility and name will be set.
        
        This method will manage some replies as well.
        """
        if hasattr(self.msg,'logistics_contact') and self.msg.logistics_contact.is_active:
            self.respond(config.Messages.ALREADY_REGISTERED)
        
        words = text.split()
        if len(words) < 3:
            self.help()
        else:
            self.contact_name = " ".join(words[:-2])
            self.extra = words[-2]
            code = words[-1]
            try:
                self.supply_point = SupplyPoint.objects.get(active=True, code__iexact=code)
            except SupplyPoint.DoesNotExist:
                self.respond(_(config.Messages.UNKNOWN_LOCATION), code=code)

        return self.responded
