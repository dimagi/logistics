#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, SupplyPoint
from logistics.apps.malawi.handlers.abstract.register import RegistrationBaseHandler
from rapidsms.contrib.locations.models import Location
from logistics.apps.malawi.exceptions import IdFormatException
from logistics.apps.logistics.util import config

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
        
        # default to HSA
        role = ContactRole.objects.get(code=config.Roles.HSA)
        
        def format_id(code, id):
            try:
                id_num = int(id)
                if id_num < 1 or id_num >= 100:
                    raise IdFormatException("id must be a number between 1 and 99. %s is out of range" % id)
                return "%s%02d" % (code, id_num)
            except ValueError:
                raise IdFormatException("id must be a number between 1 and 99. %s is not a number" % id)
        
        try:
            hsa_id = format_id(self.supply_point.code, self.extra)
        except IdFormatException, e:
            self.respond(str(e))
            return
        
        if Location.objects.filter(code=hsa_id).exists():
            self.respond("Sorry, a location with %(code)s already exists. Another HSA may have already registered this ID", code=hsa_id)
            return
        if SupplyPoint.objects.filter(code=hsa_id).exists():
            self.respond("Sorry, a supply point with %(code)s already exists. Another HSA may have already registered this ID", code=hsa_id)
            return
        
        # create a location and supply point for the HSA
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
        contact.save()
        self.msg.connection.contact = contact
        self.msg.connection.save()
        self.respond(_(config.Messages.REGISTRATION_CONFIRM), sp_name=self.supply_point.name,
                     contact_name=contact.name, role=contact.role.name)
        

