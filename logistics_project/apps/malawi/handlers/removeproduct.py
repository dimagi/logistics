from logistics.decorators import logistics_contact_and_permission_required
from django.db import transaction
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.models import Product, ProductStock
from logistics.util import config

class RemoveProductHandler(KeywordHandler):
    """
    Remove a product from an HSA.
    """

    keyword = "remove"

    def help(self):
        self.respond(config.Messages.REMOVE_HELP_MESSAGE)

    @transaction.commit_on_success
    @logistics_contact_and_permission_required(config.Operations.REMOVE_PRODUCT)
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
            # Check to make sure we're supplying this product.
            if self.hsa.supplies_product(f):
                self.hsa.deactivate_product(f)
            if f in self.msg.logistics_contact.commodities.all():
                self.msg.logistics_contact.commodities.remove(f)
                self.msg.logistics_contact.save()
        self.respond(config.Messages.REMOVE_SUCCESS_MESSAGE, products=" ".join\
                        (self.msg.logistics_contact.commodities.values_list\
                            ("sms_code", flat=True).order_by("sms_code")))
