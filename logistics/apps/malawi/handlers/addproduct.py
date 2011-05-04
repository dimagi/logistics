from logistics.apps.logistics.models import ContactRole, Product, ProductStock
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from config import Messages
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact

class AddProductHandler(KeywordHandler):
    """
    Add a product to an HSA.
    """

    keyword = "add"

    def help(self):
        self.respond(Messages.ADD_HELP_MESSAGE)

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
        already_supplied = []
        for f in found:
            # Check to make sure we're not already supplying this product.
            if self.hsa.supplies_product(f):
                already_supplied += [f]
        if len(already_supplied):
            self.respond_error(Messages.ADD_FAILURE_MESSAGE, products=" ".join([x.sms_code for x in already_supplied]))
        else:
            for f in found:
                if not ProductStock.objects.filter(supply_point=self.hsa, product=f).exists():
                    ProductStock(supply_point=self.hsa, product=f).save()
                self.hsa.activate_product(f)
            self.respond(Messages.ADD_SUCCESS_MESSAGE, products=" ".join(words))
