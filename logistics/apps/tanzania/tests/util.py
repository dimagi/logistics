from rapidsms.models import Contact
from logistics.apps.logistics.models import Product, ProductStock

def register_user(testcase, phone, name, loc_code="d10001", loc_name="Test Facility"):
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
    