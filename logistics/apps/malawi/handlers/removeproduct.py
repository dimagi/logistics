from logistics.apps.logistics.models import ContactRole, Product, ProductStock
from logistics.apps.malawi.const import Messages
from logistics.apps.logistics.const import Reports
from logistics.apps.malawi import const
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
        if len(words) < 2:
            return self.help()
        self.hsa = self.msg.logistics_contact.supply_point
        self.product_codes = words[1:]
        found = [Product.objects.get(sms_code__iexact=code) for code in self.product_codes \
                 if Product.objects.exists(sms_code__iexact=code)]
        already_supplied = []
        for f in found:
            # Check to make sure we're not already supplying this product.
            if ProductStock.objects.exists(supply_point=self.hsa, product=f) and \
                ProductStock.objects.get(supply_point=self.hsa).is_active:
                already_supplied += [f]
        if len(already_supplied):
            self.respond_error(Messages.ADD_FAILURE_MESSAGE, products=" ".join([x.sms_code for x in already_supplied]))
        else:
            for f in found:
                if not ProductStock.objects.exists(supply_point=self.hsa, product=f):
                    ProductStock(supply_point=self.hsa, product=f).save()
                self.hsa.activate_product(f)
            self.respond(Messages.ADD_SUCCESS_MESSAGE, products=" ".join(self.product_codes))

class RemoveProductHandler(KeywordHandler):
    """
    Remove a product from an HSA.
    """

    keyword = "remove"

    def help(self):
        self.respond(Messages.REMOVE_HELP_MESSAGE)

    def handle(self, text):
        words = text.split(" ")
        if len(words) < 2:
            return self.help()
        self.hsa = self.msg.logistics_contact.supply_point
        self.product_codes = words[1:]
        found = [Product.objects.get(sms_code__iexact=code) for code in self.product_codes \
                 if Product.objects.exists(sms_code__iexact=code)]
        not_supplied = []
        for f in found:
            # Check to make sure we're supplying this product.
            if not ProductStock.objects.exists(supply_point=self.hsa, product=f) or not \
                ProductStock.objects.get(supply_point=self.hsa).is_active:
                not_supplied += [f]
        if len(not_supplied):
            self.respond_error(Messages.REMOVE_FAILURE_MESSAGE, products=" ".join([x.sms_code for x in not_supplied]))
        else:
            for f in found:
                #if not ProductStock.objects.exists(supply_point=self.hsa, product=f):
                #    ProductStock(supply_point=self.hsa, product=f).save()
                self.hsa.deactivate_product(f)
            self.respond(Messages.REMOVE_SUCCESS_MESSAGE, products=" ".join(self.product_codes))
