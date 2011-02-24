#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from rapidsms.conf import settings
from django.utils.translation import ugettext as _
from logistics.apps.logistics.models import Contact, Location, REGISTER_MESSAGE

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
        if len(words) != 2:
            self.respond(_("Sorry, I didn't understand. To register, send register <name> <facility code>. Example: register john dedh'"))
            return
        name, code = words
        try:
            sdp = Location.objects.get(code__contains=code)
        except Location.DoesNotExist:
            self.respond(_("Sorry, can't find the location with FACILITY CODE %(code)s"), code=code )
            return
        contact = Contact.objects.create(name=name, location=sdp)
        self.msg.connection.contact = contact
        self.msg.connection.save()
        kwargs = {'sdp_name': sdp.name,
                  'code': code,
                  'contact_name': contact.name}
        self.respond(_("Congratulations %(contact_name)s, you have successfully been registered for the Early Warning System. Your facility is %(sdp_name)s"), **kwargs)
