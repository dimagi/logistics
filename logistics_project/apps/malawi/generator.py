from random import choice, randint, sample, normalvariate
from datetime import timedelta, datetime
from djappsettings import settings
from logistics.models import get_geography, ContactRole, SupplyPoint, Product, ProductStock, ProductReport, ProductReportType, SupplyPointType
from random import choice, randint, sample, normalvariate
from logistics.util import config
from rapidsms.contrib.httptester.utils import send_test_message
from static.malawi import config as malawi_config
from logistics.util import config
from logistics.config import hsa_supply_point_type
from rapidsms.models import Backend, Connection, Contact


MAX_HSAS_PER_FACILITY = 2
MAX_PRODUCTS_PER_HSA = 4
MAX_REPORTS_PER_HSA = 8
DAYS_OF_DATA = 50

names = ["cory", "christian", "ellie", "amos", "barbara", "boniface", \
         "drew", "danny", "jon", "anton", "ro", "carter", "ryan", \
         "dan", "amelia", "joan", "mildred", "innocent", "vincent", "noel", \
         "richard"]

def create_hsa(parent, name=None, number=None, role=None):
    hsa_code = ""
    i = 0
    # Find an unused code.
    for i in xrange(1,99):
        try:
            hsa_code = "%(facility)s%(id)02d" % {'facility': parent.code, 'id': i}
            SupplyPoint.objects.get(code=hsa_code)
        except SupplyPoint.DoesNotExist:
            break

    name = name if name else "%s_%d" % (choice(names), randint(100,999))

    identity=str(number) if number else str(randint(100000,999999))

    if role is None:
        send_test_message(identity=identity, text="register %(name)s %(id)s %(fac_id)s" %
                                            {'name': name,
                                             'id':i,
                                             'fac_id': parent.code})
        products = sample(list(Product.objects.all()), randint(1, MAX_PRODUCTS_PER_HSA))
        text = "add " + ' '.join([p.sms_code for p in products])
        print text
        send_test_message(identity=identity, text=text)
        if randint(0,3):
            m = "soh "
            for p in products:
                amc = (p.average_monthly_consumption if p.average_monthly_consumption else 100)
                m += "%s %d " % (p.sms_code, amc)
            send_test_message(identity=identity, text=m)
            print m

    else:
        send_test_message(identity=identity, text="manage %(name)s %(role)s %(fac_id)s" %
                                            {'name': name,
                                             'role':role.code,
                                             'fac_id': parent.code})
    
 #    c.is_active = True
#
#    # Create the backend.
#    if settings.DEFAULT_BACKEND:
#        backend = Backend.objects.get(name=settings.DEFAULT_BACKEND)
#    else:
#        backend = Backend.objects.all()[0]
#    conn = Connection(backend=backend, contact=c, identity=number if number else randint(100000,999999))
#    conn.save()
#
#    # Create a SupplyPoint.
#    sp = SupplyPoint()
#    sp.name = c.name
#    sp.type = hsa_supply_point_type()
#    sp.supplied_by = parent
#    sp.location = parent.location
#    sp.code = hsa_code
#    sp.save()
#
#    c.supply_point = sp
#    c.save()

    # Supply some products.

    #        ProductStock(product=p,supply_point=sp,quantity=p.average_monthly_consumption).save()
#        sp.activate_product(p)
#    sp.save()

    try:
        return SupplyPoint.objects.get(name=name)
    except SupplyPoint.DoesNotExist:
        return None

def generate_hsas():
    sps = SupplyPoint.objects.filter(active=True, type=SupplyPointType.objects.get(code="hf"))
    created = []
    sps = [sp for sp in sps if not sp.children()]
    for sp in sps:
        created += [create_hsa(sp, role=ContactRole.objects.get(code='ic'))] # in charge hsa]
        for i in xrange(0, randint(0, MAX_HSAS_PER_FACILITY)):
            created += [create_hsa(sp)]
    return created

def generate_report(hsa, date=datetime.utcnow()):
    choice = randint(1,9)
    if choice < 5:
        if not hsa or not hsa.name: return
        print "Got soh for " + hsa.name
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
    dates = [datetime.utcnow() - timedelta(days=randint(3,DAYS_OF_DATA)) for d in xrange(1,randint(1, MAX_REPORTS_PER_HSA))]
    for d in dates:
        generate_report(hsa, d)

def generate():
    hsas = generate_hsas()
    for hsa in hsas:
        if randint(0,8): # have some non-reporting HSAs
            generate_activity(hsa)
