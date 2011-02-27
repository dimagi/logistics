#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from rapidsms.conf import settings
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, Facility, REGISTER_MESSAGE

class LanguageHandler(KeywordHandler):
    """
    Allow remote users to set their preferred language, by updating the
    ``language`` field of the Contact associated with their connection.
    """

    keyword = "reg|register"

    def help(self):
        self.respond(REGISTER_MESSAGE)
    
    def handle(self, text):
        words = text.split()
        if len(words) < 2 or len(words) > 3:
            self.respond(_("Sorry, I didn't understand. To register, send register <name> <facility code>. Example: register john dwdh'"))
            return
        name = words[0]
        code = words[1]
        try:
            fac = Facility.objects.get(code__contains=code)
        except Facility.DoesNotExist:
            self.respond(_("Sorry, can't find the location with FACILITY CODE %(code)s"), code=code )
            return
        if len(words) == 3:
            role_code = words[2]
            try:
                role = ContactRole.objects.get(slug=role_code)
            except ContactRole.DoesNotExist:
                self.respond("Sorry, I don't understand the role %(role)s", role=role_code)
                return
            contact = Contact.objects.create(name=name, facility=fac, role=role)
        else:
            contact = Contact.objects.create(name=name, facility=fac)
        self.msg.connection.contact = contact
        self.msg.connection.save()
        kwargs = {'sdp_name': fac.name,
                  'code': code,
                  'contact_name': contact.name}
        self.respond(_("Congratulations %(contact_name)s, you have successfully been registered for the Early Warning System. Your facility is %(sdp_name)s"), **kwargs)
