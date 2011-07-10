"""Managers register for the system here"""
from django.utils.translation import ugettext as _
from rapidsms.models import Contact
from logistics.models import ContactRole, SupplyPoint
from logistics_project.apps.malawi.handlers.abstract.register import RegistrationBaseHandler
from logistics.util import config

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
        if self.supply_point.location.type.name != 'district' and role.code in config.Roles.DISTRICT_ONLY:
            self.respond(config.Messages.ROLE_WRONG_LEVEL, role=ContactRole.objects.get(code=self.extra).name, level=self.supply_point.location.type.name)
            return
        if self.supply_point.location.type.name != 'facility' and role.code in config.Roles.FACILITY_ONLY:
            self.respond(config.Messages.ROLE_WRONG_LEVEL, role=ContactRole.objects.get(code=self.extra).name, level=self.supply_point.location.type.name)
            return
        if role.code in config.Roles.UNIQUE and Contact.objects.filter(role=role, supply_point=self.supply_point, is_active=True).exists():
            self.respond(config.Messages.ROLE_ALREADY_FILLED, role=ContactRole.objects.get(code=self.extra).name)
            return
        # overwrite the existing contact data if it was already there
        # we know at least they were not active since we checked above
        contact = self.msg.logistics_contact if hasattr(self.msg,'logistics_contact') else Contact()
        contact.name = self.contact_name
        contact.supply_point = self.supply_point
        contact.role = role
        contact.is_active = True
        contact.is_approved = True # Bypass approval process for higher-ups
        contact.save()
        self.msg.connection.contact = contact
        self.msg.connection.save()
        self.respond(_(config.Messages.REGISTRATION_CONFIRM), sp_name=self.supply_point.name,
                     contact_name=contact.name, role=contact.role.name)
