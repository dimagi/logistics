#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from __future__ import unicode_literals
from datetime import datetime
from logistics.decorators import logistics_contact_and_permission_required
from logistics.models import StockRequest
from logistics.util import config
from logistics_project.apps.malawi.handlers.abstract.orderresponse import OrderResponseBaseHandler
from logistics_project.decorators import validate_base_level_from_supervisor


class OrderReadyHandler(OrderResponseBaseHandler):
    """
    When a supply has been ordered, it is confirmed "ready" by the person
    providing supplies with this handler.
    """

    keyword = "ready"

    @logistics_contact_and_permission_required(config.Operations.FILL_ORDER)
    @validate_base_level_from_supervisor([config.BaseLevel.HSA, config.BaseLevel.FACILITY])
    def help(self):
        if self.base_level_is_hsa:
            self.respond(config.Messages.HSA_LEVEL_ORDERREADY_HELP_MESSAGE)
        else:
            self.respond(config.Messages.FACILITY_LEVEL_ORDERREADY_HELP_MESSAGE)

    def handle_custom(self, text):
        now = datetime.utcnow()
        pending_reqs = StockRequest.pending_requests().filter(supply_point=self.supply_point)
        for req in pending_reqs:
            req.approve(self.msg.logistics_contact, now, req.amount_requested)

        if self.base_level_is_hsa:
            supply_point_name = self.contacts[0].name
        else:
            supply_point_name = self.supply_point.name

        self.respond(config.Messages.APPROVAL_RESPONSE, supply_point=supply_point_name)
        for contact in self.contacts:
            if self.base_level_is_hsa:
                contact.message(config.Messages.HSA_LEVEL_APPROVAL_NOTICE, hsa=supply_point_name)
            else:
                contact.message(config.Messages.FACILITY_LEVEL_APPROVAL_NOTICE, supply_point=supply_point_name)

        # this is really hacky, but set the SoH to non-zero for the reported products
        # so that they show no longer stocked out in things like alerts
        for req in pending_reqs:
            if self.msg.logistics_contact.supply_point.stock(req.product) == 0:
                self.msg.logistics_contact.supply_point.update_stock(req.product, 1)
