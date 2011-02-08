#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from ilsgateway.models import ContactDetail, ServiceDeliveryPoint, ContactRole
import string
import re
from django.utils.translation import ugettext_noop as _

class RegisterHandler(KeywordHandler):
    """
    Allow remote users to register themselves, by creating a Contact
    object and associating it with their Connection. For example::

        >>> RegisterHandler.test('join Adam Mckaig')
        ['Thank you for registering, Adam Mckaig!']

        >>> Contact.objects.filter(name="Adam Mckaig")
        [<Contact: Adam Mckaig>]

    Note that the ``name`` field of the Contact model is not constrained
    to be unique, so this handler does not reject duplicate names. If
    you wish to enforce unique usernames or aliases, you must extend
    Contact, disable this handler, and write your own.
    """

    keyword = "register|reg|join|sajili"

    def help(self):
        self.respond(_("To register, send register <name> <msd code>. Example: register 'john patel d34002'"))

    def handle(self, text):
        words = text.split()
        name = []
        msd_code = []
        for the_string in words:
            if re.match('^d\d+', the_string.strip().lower()):
                msd_code.append(the_string.strip().lower())
            else:
                name.append(the_string)
        name = string.join(name, ' ') 
        msd_code = string.join(msd_code, '')
        
        if not msd_code:
            self.respond(_("I didn't recognize your msd code.  To register, send register <name> <msd code>. example: register Peter Juma d34002"))
            return
        else:            
            try:
                sdp = ServiceDeliveryPoint.objects.filter(msd_code__iexact=msd_code)[0:1].get()
            except ServiceDeliveryPoint.DoesNotExist:
                kwargs = {'msd_code': msd_code}
                self.respond(_("Sorry, can't find the location with MSD CODE %(msd_code)s"), **kwargs )
                return
        
        #Default to Facility in-charge or District Pharmacist for now
        if sdp.service_delivery_point_type.name == "DISTRICT":
            role = ContactRole.objects.filter(name="District Pharmacist")[0:1].get()
        elif sdp.service_delivery_point_type.name == "FACILITY":
            role = ContactRole.objects.filter(name="Facility in-charge")[0:1].get()
            
        is_primary = True
#        if ContactDetail.objects.filter(primary=True, service_delivery_point=sdp):
#            is_primary = False
            
        contact = ContactDetail.objects.create(name=name, service_delivery_point=sdp, role=role, primary=is_primary, language="sw")
        
        self.msg.connection.contact = contact
        self.msg.connection.save()
        kwargs = {'sdp_name': sdp.name,
                  'msd_code': msd_code,
                  'contact_name': contact.name}

        self.respond(_("Thank you for registering at %(sdp_name)s, %(msd_code)s, %(contact_name)s"), **kwargs)