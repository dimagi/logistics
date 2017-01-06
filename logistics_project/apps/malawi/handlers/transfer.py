#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.models import StockTransfer
from logistics.const import Reports
from logistics.util import config
from logistics_project.apps.malawi.util import get_supply_point_and_contacts
from logistics_project.apps.malawi.validators import get_base_level_validator
from logistics.decorators import logistics_contact_and_permission_required
from logistics_project.apps.malawi.shortcuts import send_transfer_responses
from logistics.shortcuts import create_stock_report
from logistics_project.decorators import validate_base_level


class TransferHandler(KeywordHandler):
    """
    HSA to HSA transfers of products, or
    Facility to Facility transfers of products
    """

    keyword = "give"

    @logistics_contact_and_permission_required(config.Operations.MAKE_TRANSFER)
    @validate_base_level([config.BaseLevel.HSA, config.BaseLevel.FACILITY])
    def help(self):
        if self.base_level_is_hsa:
            self.respond(config.Messages.HSA_LEVEL_TRANSFER_HELP_MESSAGE)
        else:
            self.respond(config.Messages.FACILITY_LEVEL_TRANSFER_HELP_MESSAGE)

    @logistics_contact_and_permission_required(config.Operations.MAKE_TRANSFER)
    @validate_base_level([config.BaseLevel.HSA, config.BaseLevel.FACILITY])
    def handle(self, text):
        words = text.split(" ")
        # need at least a keyword and 1 product + amount
        if len(words) < 3: 
            return self.help()

        supply_point_code = words[0]
        remainder = " ".join(words[1:])
        contacts, supply_point = get_supply_point_and_contacts(supply_point_code, self.base_level)

        if not supply_point:
            if self.base_level_is_hsa:
                self.respond(config.Messages.UNKNOWN_HSA, hsa_id=supply_point_code)
            else:
                self.respond(config.Messages.UNKNOWN_FACILITY, supply_point_code=supply_point_code)
        else:
            try:
                stock_report = create_stock_report(
                    Reports.GIVE,
                    self.msg.logistics_contact.supply_point,
                    remainder,
                    self.msg.logger_msg,
                    additional_validation=get_base_level_validator(self.base_level)
                )
            except config.BaseLevel.InvalidProductsException as e:
                self.respond(config.Messages.INVALID_PRODUCTS, product_codes=e.product_codes_str)
                return

            StockTransfer.create_from_transfer_report(stock_report, supply_point)
            send_transfer_responses(self.msg, stock_report, self.msg.logistics_contact, supply_point, contacts,
                base_level=self.base_level)
