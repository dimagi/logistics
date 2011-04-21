#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from rapidsms.conf import settings
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, Facility, SupplyPoint, REGISTER_MESSAGE, SupplyPointType
from rapidsms.contrib.locations.models import Location, LocationType
from logistics.apps.malawi import const
from logistics.apps.malawi.handlers.abstract import AbstractBaseHandler

HSA_HELP_MESSAGE = "Sorry, I didn't understand. To register, send register <name> <id> <parent facility>. Example: 'register john 1 1001'"

class HSARegistrationHandler(AbstractBaseHandler):
    """
    Registration for HSAs
    """

    keyword = "reg|register"
    help_message = HSA_HELP_MESSAGE
    
    def handle(self, text):
        if self.handle_preconditions(text):
            return
        
        # default to HSA
        role = ContactRole.objects.get(code=const.ROLE_HSA)
        
        def format_id(code, id):
            # TODO, finalize this
            return "%s%s" % (code, id)
        
        hsa_id = format_id(self.supply_point.code, self.extra)
        
        if Location.objects.filter(code=hsa_id).exists():
            self.respond("Sorry, a location with %(code)s already exists. Another HSA may have already registered this ID", code=hsa_id)
            return
        if SupplyPoint.objects.filter(code=hsa_id).exists():
            self.respond("Sorry, a supply point with %(code)s already exists. Another HSA may have already registered this ID", code=hsa_id)
            return
        
        # create a location and supply point for the HSA
        hsa_loc = Location.objects.create(name=self.contact_name, type=const.hsa_location_type(),
                                          code=hsa_id, parent=self.supply_point.location)
        sp = SupplyPoint.objects.create(name=self.contact_name, code=hsa_id, type=const.hsa_supply_point_type(), 
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
        kwargs = {'sdp_name': self.supply_point.name,
                  'contact_name': contact.name}
        self.respond(_("Congratulations %(contact_name)s, you have successfully been registered for the Early Warning System. Your facility is %(sdp_name)s"), **kwargs)

