from __future__ import unicode_literals
from logistics.decorators import logistics_contact_and_permission_required
from logistics.util import config
from logistics_project.apps.malawi.handlers.abstract.products import BaseProductHandler


class AddProductHandler(BaseProductHandler):
    """
    Add a product to an HSA.
    """

    keyword = "add"

    def help(self):
        self.respond(config.Messages.ADD_HELP_MESSAGE)

    @logistics_contact_and_permission_required(config.Operations.ADD_PRODUCT)
    def handle(self, text):
        return super(AddProductHandler, self).handle(text)

    def handle_products(self, products):
        for p in products:
            self.hsa.activate_product(p)
            self.msg.logistics_contact.commodities.add(p)

        self.msg.logistics_contact.save()
        self.respond(config.Messages.ADD_SUCCESS_MESSAGE, products=" ".join\
                        (self.msg.logistics_contact.commodities.values_list\
                            ("sms_code", flat=True).order_by("sms_code")))
