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
from logistics.models import ProductStock, Product, ProductReportsHelper

class StockInquiryHandler(KeywordHandler):
    """
    """
    keyword = "si"
    
    def help(self):
        self.respond(_(config.Messages.STOCK_INQUIRY_HELP_MESSAGE))

    @logistics_contact_required()
    def handle(self, text):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point
        result = text.split()
        product_code = result[0]
        amt = result[1]
        p = Product.objects.get(product_code=product_code)
        prh = ProductReportsHelper(sp, Reports.SOH)
        prh.add_product_stock(p.sms_code, amt)
        prh.save()
        self.respond(_(config.Messages.STOCK_INQUIRY_CONFIRM) % {"quantity": amt, "product_name": p.name})