"""Managers register for the system here"""
from __future__ import unicode_literals
from django.utils.translation import gettext as _
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

    def valid_roles(self):
        return config.Roles.FACILITY_ONLY + config.Roles.DISTRICT_ONLY + config.Roles.ZONE_ONLY

    def respond_role_wrong_level(self, role):
        self.respond(config.Messages.ROLE_WRONG_LEVEL, role=role.name, level=self.supply_point.location.type.name)

    def respond_unknown_role(self, role_code):
        valid_roles = " ".join(self.valid_roles())
        self.respond(config.Messages.UNKNOWN_ROLE, role=role_code, valid_roles=valid_roles)

    def handle(self, text):
        if self.handle_preconditions(text):
            return
        
        try:
            role = ContactRole.objects.get(code__iexact=self.extra)
        except ContactRole.DoesNotExist:
            self.respond_unknown_role(self.extra)
            return

        if role.code not in self.valid_roles():
            self.respond_unknown_role(role.code)
            return

        if self.supply_point.location.type.name != config.LocationCodes.ZONE and role.code in config.Roles.ZONE_ONLY:
            self.respond_role_wrong_level(role)
            return

        if self.supply_point.location.type.name != config.LocationCodes.DISTRICT and role.code in config.Roles.DISTRICT_ONLY:
            self.respond_role_wrong_level(role)
            return

        if self.supply_point.location.type.name != config.LocationCodes.FACILITY and role.code in config.Roles.FACILITY_ONLY:
            self.respond_role_wrong_level(role)
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

        if role.code in config.Roles.ZONE_ONLY:
            self.respond(config.Messages.REGISTRATION_ZONE_CONFIRM, sp_name=self.supply_point.name,
                         contact_name=contact.name, role=contact.role.name)
        elif role.code in config.Roles.DISTRICT_ONLY:
            self.respond(_(config.Messages.REGISTRATION_DISTRICT_CONFIRM), sp_name=self.supply_point.name,
                         contact_name=contact.name, role=contact.role.name)
        else:
            self.respond(_(config.Messages.REGISTRATION_CONFIRM), sp_name=self.supply_point.name,
                         contact_name=contact.name, role=contact.role.name)
