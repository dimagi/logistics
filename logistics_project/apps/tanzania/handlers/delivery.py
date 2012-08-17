#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime, timedelta
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
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
from logistics_project.apps.tanzania.utils import send_if_connection

CHARS_IN_CODE = "2, 4"
NUMERIC_LETTERS = ("lLIoO", "11100")

class DeliveryHandler(KeywordHandler,TaggingHandler):
    """
    """
    keyword = "delivered|dlvd|nimepokea"

    def _send_delivery_alert_to_facilities(self, sp):
        for child in sp.children():
            for c in child.active_contact_set:
                send_if_connection(c, _(config.Messages.DELIVERY_CONFIRM_CHILDREN),
                                   **{"district_name": sp.name} )

    @logistics_contact_required()
    def help(self):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point

        if sp.type.code.lower() == config.SupplyPointCodes.DISTRICT:
            SupplyPointStatus.objects.create(supply_point=sp,
                                             status_type=SupplyPointStatusTypes.DELIVERY_DISTRICT,
                                             status_value=SupplyPointStatusValues.RECEIVED,
                                             status_date=self.msg.timestamp)
            self._send_delivery_alert_to_facilities(sp)
            self.respond(_(config.Messages.DELIVERY_CONFIRM_DISTRICT), **{"contact_name":contact.name,
                                                                          "facility_name":sp.name})
        elif sp.type.code.lower() == config.SupplyPointCodes.FACILITY:
            SupplyPointStatus.objects.create(supply_point=sp,
                                     status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                     status_value=SupplyPointStatusValues.RECEIVED,
                                     status_date=self.msg.timestamp)
            self.respond(_(config.Messages.DELIVERY_PARTIAL_CONFIRM))
        else:
            # TODO be graceful
            self.add_tag("Error")
            raise Exception("bad location type: %s" % sp.type.name)

    @logistics_contact_required()
    def handle(self, text):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point
        stock_report = create_stock_report(Reports.REC,
                                           sp,
                                           text,
                                           self.msg.logger_msg,
                                           timestamp=self.msg.timestamp)
        if stock_report.errors:
            for e in stock_report.errors:
                if isinstance(e, UnknownCommodityCodeError):
                    self.respond_error(_(config.Messages.INVALID_PRODUCT_CODE), **{"product_code": e})
                    return
            self.respond_error(_(config.Messages.DELIVERY_BAD_FORMAT))
            return

        else:
            expected_products = set(contact.commodities.all())

            # define missing as products not seen in the last 7 days
            # the exclusion prevents newly added products from counting as "seen"
            start_date = datetime.utcnow() + timedelta(days=-7)
            seen_products = set(Product.objects.get(pk=product_id) for product_id in \
                                ProductStock.objects.filter\
                                    (supply_point=sp, last_modified__gte=start_date)\
                                    .exclude(quantity=None)\
                                    .values_list("product", flat=True))

            self.respond(_(config.Messages.DELIVERY_CONFIRM),
                         reply_list=','.join(sorted(stock_report.reported_products())))

            SupplyPointStatus.objects.create(supply_point=sp,
                                             status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                             status_value=SupplyPointStatusValues.RECEIVED,
                                             status_date=self.msg.timestamp)
