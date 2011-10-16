from logistics.decorators import logistics_contact_and_permission_required
from logistics.models import Product, ProductStock
from logistics.util import config
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.db import transaction


class AddProductHandler(KeywordHandler):
    """
    Add a product to an HSA.
    """

    keyword = "add"

    def help(self):
        self.respond(config.Messages.ADD_HELP_MESSAGE)
        
        
    @transaction.commit_on_success
    @logistics_contact_and_permission_required(config.Operations.ADD_PRODUCT)
    def handle(self, text):
        words = text.split(" ")
        if not len(words):
            return self.help()
        self.hsa = self.msg.logistics_contact.supply_point
        for code in words:
            if not Product.objects.filter(sms_code__iexact=code).exists():
                self.respond_error(config.Messages.UNKNOWN_CODE, product=code)
                return
        for f in [Product.objects.get(sms_code__iexact=code) for code in words]:
                if not ProductStock.objects.filter(supply_point=self.hsa, product=f).exists():
                    ProductStock(supply_point=self.hsa, product=f).save()
                self.msg.logistics_contact.commodities.add(f)
                self.hsa.activate_product(f)
        self.msg.logistics_contact.save()
        self.respond(config.Messages.ADD_SUCCESS_MESSAGE, products=" ".join\
                        (self.msg.logistics_contact.commodities.values_list\
                            ("sms_code", flat=True).order_by("sms_code")))