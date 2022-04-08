"""Managers register for the system here"""
from __future__ import unicode_literals
from django.utils.translation import gettext as _
from logistics.decorators import logistics_contact_and_permission_required
from logistics_project.apps.malawi.util import get_hsa
from rapidsms.models import Contact
from logistics.models import ContactRole, SupplyPoint
from logistics_project.apps.malawi.handlers.abstract.register import RegistrationBaseHandler
from logistics.util import config
from static.malawi.config import Operations


class ApprovalHandler(RegistrationBaseHandler):
    """
    Registration for everyone else
    """
    
    keyword = "approve"
     
    def help(self):
        self.respond(config.Messages.MANAGER_HELP)

    @logistics_contact_and_permission_required(Operations.APPROVE_USER)
    def handle(self, text):

        contact = None
        try:
            contact = get_hsa(text)
        except (ContactRole.DoesNotExist, SupplyPoint.DoesNotExist):
            self.respond(config.Messages.UNKNOWN_HSA, hsa_id=text)
            return

        if contact is None: #don't see how this could happen, but check anyway
            self.respond(config.Messages.UNKNOWN_HSA, hsa_id=text)
            return

        contact.is_approved = True
        contact.save()

        contact.message(config.Messages.APPROVAL_HSA, hsa=contact.name)
        self.respond(config.Messages.APPROVAL_SUPERVISOR, hsa=contact.name)
