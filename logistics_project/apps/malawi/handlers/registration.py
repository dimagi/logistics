#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from builtins import str
from django.utils.translation import ugettext as _
from django.conf import settings
from rapidsms.models import Contact
from logistics.models import ContactRole, SupplyPoint
from logistics_project.apps.malawi.handlers.abstract.register import RegistrationBaseHandler
from rapidsms.contrib.locations.models import Location
from logistics_project.apps.malawi.exceptions import IdFormatException
from logistics.util import config
from logistics_project.apps.malawi.util import format_id
from static.malawi.config import Roles

class HSARegistrationHandler(RegistrationBaseHandler):
    """
    Registration for HSAs
    """

    keyword = "reg|register"

    def help(self):
        self.respond(config.Messages.HSA_HELP)
    
    def handle(self, text):
        if self.handle_preconditions(text):
            return

        if self.supply_point.type.code != 'hf':
            self.respond("Sorry, you tried to register at %(name)s which is not a health facility. Please specify a valid health facility code.", name=self.supply_point.name)
            return

        # default to HSA
        role = ContactRole.objects.get(code=config.Roles.HSA)
        try:
            hsa_id = format_id(self.supply_point.code, self.extra)
        except IdFormatException as e:
            self.respond(str(e))
            return

        if Location.objects.filter(code=hsa_id, is_active=True).exists():
            self.respond("Sorry, a location with %(code)s already exists. Another HSA may have already registered this ID", code=hsa_id)
            return
        if SupplyPoint.objects.filter(code=hsa_id, contact__is_active=True).exists():
            self.respond("Sorry, a supply point with %(code)s already exists. Another HSA may have already registered this ID", code=hsa_id)
            return
        
        # create a location and supply point for the HSA
        if SupplyPoint.objects.filter(code=hsa_id, type=config.hsa_supply_point_type(), active=False).exists():
            # We have a previously deactivated HSA.  Reassociate.
            sp = SupplyPoint.objects.get(code=hsa_id, type=config.hsa_supply_point_type(), active=False)
            sp.name = self.contact_name
            sp.active = True
            sp.save()
            sp.location.is_active=True
            sp.location.name = self.contact_name
            sp.location.save()
        else:
            hsa_loc = Location.objects.create(name=self.contact_name, type=config.hsa_location_type(),
                                              code=hsa_id, parent=self.supply_point.location)
            sp = SupplyPoint.objects.create(name=self.contact_name, code=hsa_id, type=config.hsa_supply_point_type(),
                                            location=hsa_loc, supplied_by=self.supply_point)
        
        # overwrite the existing contact data if it was already there
        # we know at least they were not active since we checked above
        contact = self.msg.logistics_contact if hasattr(self.msg,'logistics_contact') else Contact()
        contact.name = self.contact_name
        contact.supply_point = sp
        contact.role = role
        contact.is_active = True
        if not settings.LOGISTICS_APPROVAL_REQUIRED:
            contact.is_approved = True
        contact.save()
        self.msg.connection.contact = contact
        self.msg.connection.save()

        if settings.LOGISTICS_APPROVAL_REQUIRED:
            try:
                sh = Contact.objects.get(supply_point__location = self.supply_point.location,
                                         role=ContactRole.objects.get(code=Roles.HSA_SUPERVISOR))
                sh.message(config.Messages.APPROVAL_REQUEST, hsa=contact.name, code=hsa_id)
                self.respond(_(config.Messages.APPROVAL_WAITING), hsa=contact.name)
            except Contact.DoesNotExist:
                # If there's no HSA supervisor registered, we silently approve them.  Oh well.
                contact.is_approved = True
                self.respond(_(config.Messages.REGISTRATION_CONFIRM), sp_name=self.supply_point.name,
                            contact_name=contact.name, role=contact.role.name)
        else:
            self.respond(_(config.Messages.REGISTRATION_CONFIRM), sp_name=self.supply_point.name,
                        contact_name=contact.name, role=contact.role.name)
        

