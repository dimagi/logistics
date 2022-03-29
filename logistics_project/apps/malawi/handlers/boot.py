#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from __future__ import unicode_literals
from logistics.decorators import logistics_contact_and_permission_required
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.handlers.abstract.base import RecordResponseHandler
from django.utils.translation import ugettext as _

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from static.malawi import config

class BootHandler(RecordResponseHandler):

    keyword = "boot"

    def help(self):
        self.respond(config.Messages.BOOT_HELP)

    @logistics_contact_and_permission_required(config.Operations.REMOVE_USER)
    def handle(self, text):
        words = text.split()
        sp = None
        id = None
        c = None
        if len(words) < 1:
            self.help()
            return
        else:
            id = words[0]

        try:
            sp = SupplyPoint.objects.get(code=id, type__code=config.SupplyPointCodes.HSA)
        except SupplyPoint.DoesNotExist:
            self.respond(config.Messages.BOOT_ID_NOT_FOUND, id=id)
            return

        try:
            c = Contact.objects.get(supply_point = sp)
        except Contact.DoesNotExist:
            self.respond(config.Messages.BOOT_ID_NOT_FOUND, id=id)
            return

        c.is_active = False
        c.save()
        if sp and sp.type == config.hsa_supply_point_type():
            sp.deprecate()
            
        self.respond(config.Messages.BOOT_RESPONSE, contact=c.name)
