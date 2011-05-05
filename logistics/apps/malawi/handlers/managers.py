"""Managers register for the system here"""
from django.utils.translation import ugettext as _
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole
from logistics.apps.malawi.handlers.abstract.register import RegistrationBaseHandler
from logistics.apps.logistics.util import config

class ManagerRegistrationHandler(RegistrationBaseHandler):
    """
    Registration for everyone else
    """
    
    keyword = "manage"
     
    def help(self):
        self.respond(config.Messages.MANAGER_HELP)
    
    def handle(self, text):
        if self.handle_preconditions(text):
            return
        
        try:
            role = ContactRole.objects.get(code__iexact=self.extra)
        except ContactRole.DoesNotExist:
            self.respond(config.Messages.UNKNOWN_ROLE, role=self.extra,
                         valid_roles=" ".join(ContactRole.objects.values_list\
                                              ("code", flat=True).order_by("code")))
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
        self.respond(_(config.Messages.REGISTRATION_CONFIRM), sp_name=self.supply_point.name,
                     contact_name=contact.name, role=contact.role.name)
