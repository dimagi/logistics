#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from __future__ import unicode_literals
from builtins import str
from django.utils.translation import gettext as _
from logistics.decorators import logistics_contact_and_permission_required
from logistics_project.apps.malawi.handlers.abstract.base import RecordResponseHandler
from rapidsms.models import Contact
from logistics.models import ContactRole, SupplyPoint
from rapidsms.contrib.locations.models import Location
from logistics_project.apps.malawi.exceptions import IdFormatException
from static.malawi import config


class CreateUserHandler(RecordResponseHandler):
    """
    Registration for HSAs
    """

    keyword = "hsa"
    
    def help(self):
        self.respond(config.Messages.HSA_HELP)

    @logistics_contact_and_permission_required(config.Operations.ADD_USER)
    def handle(self, text):
        words = text.split()
        if len(words) < 3:
            self.help()
        else:
            self.contact_name = " ".join(words[:-2])
            self.extra =   words[-2]
            code = words[-1]
            try:
                self.supply_point = SupplyPoint.objects.get(code__iexact=code, type__code=config.SupplyPointCodes.FACILITY)
            except SupplyPoint.DoesNotExist:
                self.respond(_(config.Messages.UNKNOWN_LOCATION), code=code )
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
        except IdFormatException as e:
            self.respond(str(e))
            return
        
        if Location.objects.filter(code=hsa_id).exists():
            self.respond("Sorry, a location with %(code)s already exists. Another HSA may have already registered this ID", code=hsa_id)
            return
        if SupplyPoint.objects.filter(code=hsa_id, contact__is_active=True).exists():
            self.respond("Sorry, a supply point with %(code)s already exists. Another HSA may have already registered this ID", code=hsa_id)
            return
        
        # create a location and supply point for the HSA
        hsa_loc = Location.objects.create(name=self.contact_name, type=config.hsa_location_type(),
                                          code=hsa_id, parent=self.supply_point.location)
        sp = SupplyPoint.objects.create(name=self.contact_name, code=hsa_id, type=config.hsa_supply_point_type(), 
                                        location=hsa_loc, supplied_by=self.supply_point)
        
        # overwrite the existing contact data if it was already there
        # we know at least they were not active since we checked above
        contact =  Contact()
        contact.name = self.contact_name
        contact.supply_point = sp
        contact.role = role
        contact.is_active = True
        contact.save()
        self.respond(_(config.Messages.REGISTRATION_CONFIRM), sp_name=self.supply_point.name,
                     contact_name=contact.name, role=contact.role.name)
        

