#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from rapidsms.conf import settings
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, Facility, REGISTER_MESSAGE,\
    SupplyPoint

HELP_MESSAGE = "Sorry, I didn't understand. To register, send register <name> <facility code>. Example: register john dwdh'"
class RegistrationHandler(KeywordHandler):
    """
    Allow remote users to set their preferred language, by updating the
    ``language`` field of the Contact associated with their connection.
    """

    keyword = "reg|register"

    def help(self):
        self.respond(_(HELP_MESSAGE))
    
    def handle(self, text):
        words = text.split()
        if len(words) < 2 or len(words) > 3:
            self.respond(_(HELP_MESSAGE))
            return
        name = words[0]
        code = words[1]
        try:
            fac = SupplyPoint.objects.get(code__iexact=code)
        except SupplyPoint.DoesNotExist:
            self.respond(_("Sorry, can't find the location with CODE %(code)s"), code=code )
            return
        if len(words) == 3:
            role_code = words[2]
            try:
                role = ContactRole.objects.get(code=role_code)
            except ContactRole.DoesNotExist:
                self.respond("Sorry, I don't understand the role %(role)s", role=role_code)
                return
            contact = Contact.objects.create(name=name, supply_point=fac, role=role)
        else:
            contact = Contact.objects.create(name=name, supply_point=fac)
        self.msg.connection.contact = contact
        self.msg.connection.save()
        kwargs = {'sdp_name': fac.name,
                  'code': code,
                  'contact_name': contact.name}
        self.respond(_("Congratulations %(contact_name)s, you have successfully been registered for the Early Warning System. Your facility is %(sdp_name)s"), **kwargs)
