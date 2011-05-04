from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, Product, ProductStock
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from config import Messages

class RemoveProductHandler(KeywordHandler):
    """
    Remove a product from an HSA.
    """

    keyword = "remove"

    def help(self):
        self.respond(Messages.REMOVE_HELP_MESSAGE)

    def handle(self, text):
        words = text.split(" ")
        if not len(words):
            return self.help()
        self.hsa = self.msg.logistics_contact.supply_point
        for code in words:
            if not Product.objects.filter(sms_code__iexact=code).exists():
                self.respond_error(Messages.UNKNOWN_CODE, product=code)
                return
        found = [Product.objects.get(sms_code__iexact=code) for code in words]
        not_supplied = []
        for f in found:
            # Check to make sure we're supplying this product.
            if not self.hsa.supplies_product(f):
                not_supplied += [f]
        if len(not_supplied):
            self.respond_error(Messages.REMOVE_FAILURE_MESSAGE, products=" ".join([x.sms_code for x in not_supplied]))
        else:
            for f in found:
                self.hsa.deactivate_product(f)
            self.respond(Messages.REMOVE_SUCCESS_MESSAGE, products=" ".join(words))
