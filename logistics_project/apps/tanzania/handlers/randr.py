#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime, timedelta
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.db.models import Q
from django.utils.translation import ugettext as _
from logistics.util import config
from logistics.shortcuts import create_stock_report
from logistics.const import Reports
from logistics.decorators import logistics_contact_required
import logging
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from logistics.models import ProductStock, Product
from logistics.errors import UnknownCommodityCodeError

CHARS_IN_CODE = "2, 4"
NUMERIC_LETTERS = ("lLIoO", "11100")

class RandRHandler(KeywordHandler):
    """
    """
    keyword = "submitted|nimetuma"

    @logistics_contact_required()
    def help(self):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point

        if sp.type.code.lower() == config.SupplyPointCodes.DISTRICT:
            SupplyPointStatus.objects.create(supply_point=sp,
                                     status_type=SupplyPointStatusTypes.R_AND_R_DISTRICT,
                                     status_value=SupplyPointStatusValues.SUBMITTED,
                                     status_date=self.msg.timestamp)
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

