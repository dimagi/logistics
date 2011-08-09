#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime, timedelta
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.db.models import Q
from django.utils.translation import ugettext as _
from logistics.apps.logistics.util import config
from logistics.apps.logistics.shortcuts import create_stock_report
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.decorators import logistics_contact_required
import logging
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from logistics.apps.logistics.models import ProductStock, Product

CHARS_IN_CODE = "2, 4"
NUMERIC_LETTERS = ("lLIoO", "11100")

class DeliveryHandler(KeywordHandler):
    """
    """
    keyword = "delivered|dlvd|nimepokea"

    @logistics_contact_required()
    def help(self):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point

        SupplyPointStatus.objects.create(supply_point=sp,
                                 status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                 status_value=SupplyPointStatusValues.RECEIVED,
                                 status_date=datetime.utcnow())
        self.respond(_(config.Messages.DELIVERY_PARTIAL_CONFIRM))

    @logistics_contact_required()
    def handle(self, text):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point
        stock_report = create_stock_report(Reports.REC,
                                           sp,
                                           text,
                                           self.msg.logger_msg)

        if stock_report.errors:
            self.respond(_(config.Messages.DELIVERY_BAD_FORMAT))
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
                                             status_date=datetime.utcnow())