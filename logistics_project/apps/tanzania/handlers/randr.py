#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _
from logistics.util import config
from logistics.decorators import logistics_contact_required
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from rapidsms.models import Contact

CHARS_IN_CODE = "2, 4"
NUMERIC_LETTERS = ("lLIoO", "11100")

class RandRHandler(KeywordHandler):
    """
    """
    keyword = "submitted|nimetuma"

    def _send_submission_alert_to_msd(self, sp, submitted_vals):
        for c in Contact.objects.filter\
            (role__code=config.Roles.MSD):
            c.message(config.Messages.SUBMITTED_NOTIFICATION_MSD,
                      district_name=sp.name,
                      group_a=submitted_vals["a"],
                      group_b=submitted_vals["b"],
                      group_c=submitted_vals["c"])

    @logistics_contact_required()
    def help(self):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point

        if sp.type.code.lower() == config.SupplyPointCodes.DISTRICT:
            SupplyPointStatus.objects.create(supply_point=sp,
                                     status_type=SupplyPointStatusTypes.R_AND_R_DISTRICT,
                                     status_value=SupplyPointStatusValues.SUBMITTED,
                                     status_date=self.msg.timestamp)
            submitted_vals = {"a":"0",
                              "b":"0",
                              "c":"0"}
            self._send_submission_alert_to_msd(sp, submitted_vals)
            self.respond(_(config.Messages.SUBMITTED_REMINDER_DISTRICT))
        elif sp.type.code.lower() == config.SupplyPointCodes.FACILITY:
            SupplyPointStatus.objects.create(supply_point=sp,
                                     status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                     status_value=SupplyPointStatusValues.SUBMITTED,
                                     status_date=self.msg.timestamp)
            self.respond(_(config.Messages.SUBMITTED_CONFIRM) % {"sdp_name":sp.name, "contact_name":contact.name})
        else:
            # TODO be graceful
            raise Exception("bad location type: %s" % sdp.type.name)

    @logistics_contact_required()
    def handle(self, text):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point

        if sp.type.code.lower() == config.SupplyPointCodes.DISTRICT:
            vals = text.split()
            submitted_vals = {"a":vals[1],
                              "b":vals[3],
                              "c":vals[5]}

            SupplyPointStatus.objects.create(supply_point=sp,
                                     status_type=SupplyPointStatusTypes.R_AND_R_DISTRICT,
                                     status_value=SupplyPointStatusValues.SUBMITTED,
                                     status_date=self.msg.timestamp)
            self._send_submission_alert_to_msd(sp, submitted_vals)
            self.respond(_(config.Messages.SUBMITTED_REMINDER_DISTRICT))
        elif sp.type.code.lower() == config.SupplyPointCodes.FACILITY:
            SupplyPointStatus.objects.create(supply_point=sp,
                                     status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                     status_value=SupplyPointStatusValues.SUBMITTED,
                                     status_date=self.msg.timestamp)
            self.respond(_(config.Messages.SUBMITTED_CONFIRM) % {"sdp_name":sp.name, "contact_name":contact.name})
        else:
            # TODO be graceful
            raise Exception("bad location type: %s" % sdp.type.name)


