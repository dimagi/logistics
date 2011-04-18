#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from rapidsms.conf import settings
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, Facility, SupplyPoint, REGISTER_MESSAGE, SupplyPointType
from rapidsms.contrib.locations.models import Location, LocationType

HELP_MESSAGE = "Sorry, I didn't understand. To register, send register <name> <id> <parent facility>. Example: register john 115 dwdh'"
class HSARegistrationHandler(KeywordHandler):
    """
    Allow remote users to set their preferred language, by updating the
    ``language`` field of the Contact associated with their connection.
    """

    keyword = "hsareg|hsaregister"

    def help(self):
        self.respond(_(HELP_MESSAGE))
    
    def handle(self, text):
        words = text.split()
        if len(words) < 3 or len(words) > 4:
            self.respond(_(HELP_MESSAGE))
            return
        name = words[0]
        id =   words[1]
        code = words[2]
        try:
            fac = SupplyPoint.objects.get(code__iexact=code)
        except SupplyPoint.DoesNotExist:
            self.respond(_("Sorry, can't find the location with FACILITY CODE %(code)s"), code=code )
            return

        role = None
        if len(words) == 4:
            role_code = words[3]
            try:
                role = ContactRole.objects.get(code=role_code)
            except ContactRole.DoesNotExist:
                self.respond("Sorry, I don't understand the role %(role)s", role=role_code)
                return

        # create a location and supply point for the HSA
        hsa_loc = Location.objects.create(name=name, type=LocationType.objects.get(slug="hsa"), 
                                          code=id, parent=fac.location)
        sp = SupplyPoint.objects.create(name=name, code=id, type=SupplyPointType.objects.get(pk="hsa"), 
                                        location=hsa_loc, supplied_by=fac)

        if role:
            contact = Contact.objects.create(name=name, supply_point=sp, role=role)
        else:
            contact = Contact.objects.create(name=name, supply_point=sp)
        self.msg.connection.contact = contact
        self.msg.connection.save()
        kwargs = {'sdp_name': fac.name,
                  'code': code,
                  'contact_name': contact.name}
        self.respond(_("Congratulations %(contact_name)s, you have successfully been registered for the Early Warning System. Your facility is %(sdp_name)s"), **kwargs)
