#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from rapidsms.conf import settings
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, Facility

REGISTER_MESSAGE = "To register, send REG <NAME>. Example: 'REG Mary Phiri'"
ERROR_MESSAGE = "Sorry, did not understand. %(REG)s"  % {"REG": REGISTER_MESSAGE}
ALREADY_REGISTERED = "Sorry, this phone has already been registered to %(contact_name)s."

class LanguageHandler(KeywordHandler):
    """
    Allow remote users to set their preferred language, by updating the
    ``language`` field of the Contact associated with their connection.
    """

    keyword = "reg|register"

    def help(self):
        self.respond(REGISTER_MESSAGE)
    
    def handle(self, text):
        if self.msg.contact is not None:
            self.respond(ALREADY_REGISTERED, **{"contact_name": self.msg.contact.name})
        else:
            name = " ".join(w.capitalize() for w in text.split())
            contact = Contact.objects.create(name=name)
            self.msg.connection.contact = contact
            self.msg.connection.save()
            kwargs = {'contact_name': contact.name}
            self.respond(_("Congratulations %(contact_name)s, you have successfully been registered for the Stock Alert System."), **kwargs)
