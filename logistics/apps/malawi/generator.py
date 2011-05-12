from datetime import timedelta, datetime
from djappsettings import settings
from logistics.apps.logistics.models import get_geography, ContactRole, SupplyPoint, Product, ProductStock, ProductReport, STOCK_ON_HAND_REPORT_TYPE, ProductReportType, RECEIPT_REPORT_TYPE, SupplyPointType
from random import choice, randint, sample, normalvariate
from logistics.apps.logistics.util import config
from static.malawi import config as malawi_config
from logistics.config import hsa_supply_point_type
from rapidsms.models import Backend, Connection, Contact


MAX_HSAS_PER_FACILITY = 4
MAX_PRODUCTS_PER_HSA = 10
MAX_REPORTS_PER_HSA = 15
DAYS_OF_DATA = 100

names = ["cory", "christian", "ellie", "amos", "barbara", "boniface", \
         "drew", "danny", "jon", "anton", "ro", "carter", "ryan", \
         "dan", "amelia"]

def create_hsa(parent, name=None, number=None, role=None):
    hsa_code = ""
    i = 0
    # Find an unused code.
    for i in xrange(0,99):
        try:
            hsa_code = "%(facility)s%(id)02d" % {'facility': parent.code, 'id': i}
            SupplyPoint.objects.get(code=hsa_code)
        except SupplyPoint.DoesNotExist:
            break

    c = Contact()
    c.name = name if name else "%s_%d" % (choice(names), randint(100,999))
    c.role = role if role else ContactRole.objects.get(code=malawi_config.Roles.HSA)

    # Create the backend.
    if settings.DEFAULT_BACKEND:
        backend = Backend.objects.get(name=settings.DEFAULT_BACKEND)
    else:
        backend = Backend.objects.all()[0]
    conn = Connection(backend=backend, contact=c, identity=number if number else randint(100000,999999))
    conn.save()

    # Create a SupplyPoint.
    sp = SupplyPoint()
    sp.name = c.name
    sp.type = hsa_supply_point_type()
    sp.supplied_by = parent
    sp.location = parent.location
    sp.code = hsa_code
    sp.save()

    # Supply some products.
    products = sample(list(Product.objects.all()), randint(1, MAX_PRODUCTS_PER_HSA))
    for p in products:
        ProductStock(product=p,supply_point=sp,quantity=p.average_monthly_consumption).save()
        sp.activate_product(p)
    sp.save()

    return sp

def generate_hsas():
    sps = SupplyPoint.objects.filter(type=SupplyPointType.objects.get(code="hf"))
    created = []
    for sp in sps:
            for i in xrange(0, randint(0, MAX_HSAS_PER_FACILITY)):
                created += [create_hsa(sp)]
    return created

def generate_report(hsa, date=datetime.utcnow()):
    choice = randint(1,9)
    if choice < 5:
        print "Got soh"
        print ProductStock.objects.filter(supply_point=hsa)
        # SOH
        for p in ProductStock.objects.filter(supply_point=hsa):
            amc = (p.product.average_monthly_consumption if p.product.average_monthly_consumption else 100)
            q = p.quantity if p.quantity else amc
            q = max(0, q - normalvariate(q/3, q/6)) if randint(0,6) else 0
            print "Generating SOH report for %s : %s : %d" % (hsa.name, p.product.sms_code, q)
            r = ProductReport(product=p.product, report_type = ProductReportType.objects.get(code='soh'),
                          quantity=q, message=None, supply_point=hsa, report_date=date)
            r.save()
    elif choice < 10:
        # REC
        for p in ProductStock.objects.filter(supply_point=hsa):
            amc = (p.product.average_monthly_consumption if p.product.average_monthly_consumption else 100)
            q = normalvariate(amc, amc / 4)
            print "Generating REC report for %s : %s : %d" % (hsa.name, p.product.sms_code, q)
            r = ProductReport(product=p.product, report_type = ProductReportType.objects.get(code='rec'),
                          quantity=q, message=None, supply_point=hsa, report_date=date)
            r.save()
    else:
        pass
#        # TRANSFER
#        p = choice(ProductStock.objects.filter(supply_point=hsa))
#        amc = (p.product.average_monthly_consumption if p.product.average_monthly_consumption else 100)
#        q = max(1,normalvariate(amc/4, amc/8))
#        r = ProductReport(product=p.product, report_type = ProductReportType.objects.get(code='give'),
#                      quantity=q, message=None, supply_point=hsa, report_date=date)
#        r.save()



def generate_activity(hsa):
    for i in xrange(1, randint(1, MAX_REPORTS_PER_HSA)):
        dates = datetime.utcnow() - timedelta(days=randint(3,DAYS_OF_DATA))


        generate_report(hsa, datetime.utcnow()-)

def generate():
    hsas = generate_hsas()
    for hsa in hsas:
        if (randint(0,8)): # have some non-reporting HSAs
            generate_activity(hsa)
