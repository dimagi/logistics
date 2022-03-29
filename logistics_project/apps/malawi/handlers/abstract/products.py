from __future__ import unicode_literals
from django.db import transaction
from logistics.models import Product
from logistics.util import config
from logistics_project.decorators import validate_base_level
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class BaseProductHandler(KeywordHandler):

    @transaction.atomic
    @validate_base_level([config.BaseLevel.HSA])
    def handle(self, text):
        words = text.split(" ")
        if not len(words):
            return self.help()

        self.hsa = self.msg.logistics_contact.supply_point
        products = []
        for code in words:
            try:
                products.append(Product.objects.get(sms_code__iexact=code, type__base_level=self.base_level))
            except Product.DoesNotExist:
                self.respond_error(config.Messages.UNKNOWN_CODE, product=code)
                return

        self.handle_products(products)

    def handle_products(self, products):
        raise NotImplementedError()
