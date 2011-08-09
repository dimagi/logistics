from rapidsms.models import Contact
from logistics.apps.logistics.models import Product, ProductStock
from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase

def register_user(testcase, phone, name, loc_code="d10001", loc_name="VETA 1"):
    """
    Test utility to register a user
    """
    
    script = """
          %(phone)s > sajili %(name)s %(loc_code)s
          %(phone)s < Asante kwa kujisajili katika %(loc_name)s, %(loc_code)s, %(name)s
        """ % {"phone": phone, "name": name,
               "loc_code": loc_code, "loc_name": loc_name}
    testcase.runScript(script)
    return Contact.objects.get(connection__identity=phone)

def add_products(contact, products):
    """
    Adds products to a contact
    """
    for product_code in products:
        product = Product.objects.get(sms_code__iexact=product_code)
        if not ProductStock.objects.filter(supply_point=contact.supply_point, product=product).exists():
            ProductStock(supply_point=contact.supply_point, product=product).save()
            contact.commodities.add(product)
    contact.save()

class TestUtilities(TanzaniaTestScriptBase):

    def testRegisterUser(self):
        count = Contact.objects.count()
        contact = register_user(self, "778", "someone")
        self.assertEqual(count + 1, Contact.objects.count())
        self.assertEqual("778", contact.default_connection.identity)
        self.assertEqual("someone", contact.name)
        
    def testAddProducts(self):
        ProductStock.objects.all().delete()
        contact = register_user(self, "778", "someone")
        self.assertEqual(0, ProductStock.objects.count())
        
        add_products(contact, ["id", "dp", "ip"])
        self.assertEqual(3, ProductStock.objects.count())
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertFalse(ps.quantity)
        