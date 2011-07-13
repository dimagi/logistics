import os
import sys
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point
from dimagi.utils.couch.database import get_db
from logistics.const import Reports
from logistics.models import SupplyPoint, SupplyPointType, ProductStock, \
    ProductReportType, ContactRole, Product, ProductType
from logistics.util import config

def load_products():
    from logistics.models import Product, ProductType
    product_types = {'m':'Malaria'}
    products = [('yellow','Yellow ACT','m','box',10), 
                ('blue','Blue ACT','m','box',10), 
                ('brown','Brown ACT','m','box',10), 
                ('green','Green ACT','m','box',10), 
                ('other','Other ACT','m','box',10), ]
    for key in product_types.keys():
        t, created = ProductType.objects.get_or_create(code=key, name=product_types[key])
    for prod in products:
        p, created = Product.objects.get_or_create(sms_code=prod[0], name=prod[1], 
                                                   type=ProductType.objects.get(code=prod[2]), 
                                                   units=prod[3], 
                                                   average_monthly_consumption=prod[4])
        if created:
            print "Created product %(prod)s" % {'prod':p}

def generate_codes_for_locations():
    from rapidsms.contrib.locations.models import Location
    locs = Location.objects.all().order_by('name')
    for loc in locs:
        if loc.code is None or len(loc.code) == 0:
            loc.code = _generate_location_code(loc.name)
            loc.save()
            print "  %(name)s's code is %(code)s" % {'name':loc.name,
                                                     'code':loc.code}

def _generate_location_code(name):
    from rapidsms.contrib.locations.models import Location
    code = name.lower().replace(' ','_')
    code = code.replace('().&,','')
    postfix = ''
    existing = Location.objects.filter(code=code)
    if existing:
        count = 1
        postfix = str(count)
        try:
            while True:
                Location.objects.get(code=(code + postfix))
                count = count + 1
                postfix = str(count)
        except Location.DoesNotExist:
            pass
    return code + postfix

def init_reports(log_to_console=False):
    """
    Initialize any data that should be static here
    """
    # These are annoyingly necessary to live in the DB, currently. 
    # Really this should be app logic, I think.
    for code, name in Reports.ALL_REPORTS.items():
        prod = ProductReportType.objects.get_or_create(code=code)[0]
        if prod.name != name:
            prod.name = name
            prod.save()

def init_roles(log_to_console=False):
    for code, name in config.Roles.ALL_ROLES.items():
        role = ContactRole.objects.get_or_create(code=code)[0]
        if role.name != name:
            role.name = name
            role.save()

def init_test_location_and_supplypoints():
    location, created = Location.objects.get_or_create(name='Dangme East', 
                                                       code='de')
    gar, created = Location.objects.get_or_create(name='Greater Accra Region', 
                                                  code='gar')
    hctype, created = SupplyPointType.objects.get_or_create(code='hc')
    rmstype, created = SupplyPointType.objects.get_or_create(code='rms')
    try:
        dedh = SupplyPoint.objects.get(code='dedh')
    except SupplyPoint.DoesNotExist:
        dedh, created = SupplyPoint.objects.get_or_create(code='dedh', 
                                                          name='Dangme East District Hospital',
                                                          location=location, active=True,
                                                          type=hctype, supplied_by=None)
    try:
        rms = SupplyPoint.objects.get(code='garms')
    except SupplyPoint.DoesNotExist:
        rms, created = SupplyPoint.objects.get_or_create(code='garms', name="GARMS", 
                                                         type=rmstype, 
                                                         location=gar)
    dedh.supplied_by = rms
    dedh.save()

def init_test_product_and_stock():
    fp, created = ProductType.objects.get_or_create(code='fp', name="Family Planning")
    ov, created = Product.objects.get_or_create(sms_code='ov', name='Overette',
                                                type=fp, units='cycle', 
                                                average_monthly_consumption=5)
    ml, created = Product.objects.get_or_create(sms_code='ml', name='Microlut',
                                                type=fp, units='cycle', 
                                                average_monthly_consumption=5)
    ml.equivalents.add(ov)
    sp = SupplyPoint.objects.all()[0]
    ps, created = ProductStock.objects.get_or_create(product=ov, supply_point=sp, 
                                       manual_monthly_consumption=None, 
                                       use_auto_consumption=False)
    ps, created = ProductStock.objects.get_or_create(product=ml, supply_point=sp, 
                                       manual_monthly_consumption=None, 
                                       use_auto_consumption=False)
