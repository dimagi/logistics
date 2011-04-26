"""Managers register for the system here"""
from logistics.apps.logistics.models import ContactRole
from rapidsms.models import Contact
from django.utils.translation import ugettext as _
from logistics.apps.malawi.handlers.abstract.register import RegistrationBaseHandler
from logistics.apps.malawi.const import Messages

class ManagerRegistrationHandler(RegistrationBaseHandler):
    """
    Registration for everyone else
    """
    
    keyword = "manage"
     
    def help(self):
        self.respond(Messages.MANAGER_HELP)
    
    def handle(self, text):
        if self.handle_preconditions(text):
            return
        
        try:
            role = ContactRole.objects.get(code__iexact=self.extra)
        except ContactRole.DoesNotExist:
            self.respond("Sorry, I don't understand the role %(role)s", role=self.extra)
            return

        # overwrite the existing contact data if it was already there
        # we know at least they were not active since we checked above
        contact = self.msg.logistics_contact if hasattr(self.msg,'logistics_contact') else Contact()
        contact.name = self.contact_name
        contact.supply_point = self.supply_point
        contact.role = role
        contact.is_active = True
        contact.save()
        self.msg.connection.contact = contact
        self.msg.connection.save()
        kwargs = {'sdp_name': self.supply_point.name,
                  'contact_name': contact.name}
        self.respond(_("Congratulations %(contact_name)s, you have successfully been registered for the Early Warning System. Your facility is %(sdp_name)s"), **kwargs)
