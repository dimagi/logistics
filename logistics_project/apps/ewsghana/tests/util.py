from rapidsms.tests.scripted import TestScript
from rapidsms.models import Contact
from logistics.models import SupplyPointType, \
    ProductReportType, SupplyPoint, Product, ProductStock, \
    ProductType
from rapidsms.contrib.locations.models import Location
from logistics.const import Reports
from logistics.util import config

def load_test_data():
    try:
        pr = ProductReportType.objects.get(code=Reports.SOH)
    except ProductReportType.DoesNotExist:
        pr = ProductReportType.objects.create(code=Reports.SOH, 
                                              name=Reports.SOH)
    location, created = Location.objects.get_or_create(name='Dangme East', 
                                                       code='de')
    gar, created = Location.objects.get_or_create(name='Greater Accra Region', 
                                                  code='gar')
    hctype, created = SupplyPointType.objects.get_or_create(code='hc')
    rmstype, created = SupplyPointType.objects.get_or_create(code='rms')
    try:
        rms = SupplyPoint.objects.get(code='garms')
    except SupplyPoint.DoesNotExist:
        rms, created = SupplyPoint.objects.get_or_create(code='garms', name="GARMS", 
                                                         type=rmstype, 
                                                         location=gar)
    try:
        dedh = SupplyPoint.objects.get(code='dedh')
    except SupplyPoint.DoesNotExist:
        dedh, created = SupplyPoint.objects.get_or_create(code='dedh', 
                                                          name='Dangme East District Hospital',
                                                          location=location, active=True,
                                                          type=hctype, supplied_by=rms)
    fp, created = ProductType.objects.get_or_create(code='fp', name="Family Planning")
    ov, created = Product.objects.get_or_create(sms_code='ov', name='Overette',
                                                type=fp, units='cycle')
    ml, created = Product.objects.get_or_create(sms_code='ml', name='Microlut',
                                                type=fp, units='cycle')
    ml.equivalents.add(ov)
    ps, created = ProductStock.objects.get_or_create(product=ov, supply_point=dedh, 
                                       manual_monthly_consumption=10, 
                                       use_auto_consumption=False)
    ps, created = ProductStock.objects.get_or_create(product=ml, supply_point=dedh, 
                                       manual_monthly_consumption=10, 
                                       use_auto_consumption=False)
    
def register_user(testcase, phone, name, loc_code="dedh", loc_name="Dangme East District Hospital"):
    """
    Test utility to register a user
    """
    
    script = """
          %(phone)s > register %(name)s %(loc_code)s
          %(phone)s < Congratulations %(name)s, you have successfully been registered for the Early Warning System. Your facility is %(loc_name)s
        """ % {"phone": phone, "name": name,
               "loc_code": loc_code, "loc_name": loc_name}
    testcase.runScript(script)
    return Contact.objects.get(connection__identity=phone)

def report_stock(testcase, contact, stock, amount):
    """
    Test utility to register a user
    """
    script = """
          %(phone)s > %(stock_code)s %(amount)s
          %(phone)s < Dear %(name)s, thank you for reporting the commodities you have in stock.
        """ % {"stock_code": stock.sms_code, "amount": amount, 
               "phone":contact.default_connection.identity, "name":contact.name}
    testcase.runScript(script)
