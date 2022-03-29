from __future__ import unicode_literals
from logistics.decorators import logistics_contact_and_permission_required
from logistics.util import config
from logistics_project.apps.malawi.handlers.abstract.products import BaseProductHandler


class RemoveProductHandler(BaseProductHandler):
    """
    Remove a product from an HSA.
    """

    keyword = "remove"

    def help(self):
        self.respond(config.Messages.REMOVE_HELP_MESSAGE)

    @logistics_contact_and_permission_required(config.Operations.REMOVE_PRODUCT)
    def handle(self, text):
        return super(RemoveProductHandler, self).handle(text)

    def handle_products(self, products):
        for p in products:
            # Check to make sure we're supplying this product.
            if self.hsa.supplies_product(p):
                self.hsa.deactivate_product(p)
            if p in self.msg.logistics_contact.commodities.all():
                self.msg.logistics_contact.commodities.remove(p)
                self.msg.logistics_contact.save()

        self.respond(config.Messages.REMOVE_SUCCESS_MESSAGE, products=" ".join\
                        (self.msg.logistics_contact.commodities.values_list\
                            ("sms_code", flat=True).order_by("sms_code")))
