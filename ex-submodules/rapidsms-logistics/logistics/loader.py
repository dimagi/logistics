from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import os
import sys
from django.conf import settings
from django.db.models import Q
from django.template.defaultfilters import slugify
from rapidsms.contrib.locations.models import Location
from logistics.models import SupplyPoint, SupplyPointType, ProductStock, \
    ProductReportType, Product, ProductType
from logistics.util import config

def load_products_into_facilities(demo=False):
    import random
    from logistics.models import SupplyPoint, ProductStock, Product
    facilities = SupplyPoint.objects.order_by('type')
    if demo:
        facility_consumption = 10
        max_facility_consumption = 33
    else:
        facility_consumption = None
    for fac in facilities:
        ps_loaded = 0
        products = Product.objects.all()
        for product in products:
            try:
                ps = ProductStock.objects.get(supply_point=fac, product=product)
            except ProductStock.DoesNotExist:
                # no preexisting product stock, which is fine.
                pass
            else:
                # don't touch product stocks which exist already
                continue
            # facilities get all products by default active, 10 stock
            quantity = None
            if demo:
                quantity = random.randint(0,max_facility_consumption)
            ProductStock(quantity=quantity, 
                         is_active=True,
                         supply_point=fac,
                         product=product,
                         monthly_consumption=facility_consumption).save()
            ps_loaded += 1
        if ps_loaded > 0:
            print("Loaded %(count)s stocks into %(fac)s" % {'count':ps_loaded, 'fac':fac.name})


def load_products(log_to_console=False):
    """ Creates both products and product types """
    from logistics.models import Product, ProductType
    from logistics.util import config
    for key in list(config.ProductTypes.ALL.keys()):
        t, created = ProductType.objects.get_or_create(code=key, 
                                                       name=config.ProductTypes.ALL[key])
    for key in list(config.Products.ALL.keys()):
        try: 
            p = Product.objects.get(sms_code=key)
        except Product.DoesNotExist:
            p, created = Product.objects.get_or_create(sms_code=key, 
                                                       name=config.Products.ALL[key][0], 
                                                       type=ProductType.objects.get(code=config.Products.ALL[key][1]), 
                                                       units=config.Products.ALL[key][2], 
                                                       average_monthly_consumption=10)
        if created and log_to_console:
            print("Created product %(prod)s" % {'prod':p})

def generate_codes_for_locations(log_to_console=False):
    """ CVS doesn't require locations to have a code, but logistics
    assumes that location does, so we generate codes where they are missing
      """
    from rapidsms.contrib.locations.models import Location
    locs = Location.objects.filter(Q(code=None)|Q(code='')).order_by('name')
    for loc in locs:
        loc.code = _generate_location_code(loc.name)
        loc.save()
        if log_to_console:
            print("  %(name)s's code is %(code)s" % {'name':loc.name,
                                                     'code':loc.code})

def _generate_location_code(name, lower=True, check_existing=True, kls=Location):
    if lower:
        name = name.lower()
    code = slugify(name)
    postfix = ''
    if check_existing:
        existing = kls.objects.filter(code=code).count()
        if existing:
            count = 1
            postfix = str(count)
            try:
                while True:
                    kls.objects.get(code=(code + postfix))
                    count = count + 1
                    postfix = str(count)
            except kls.DoesNotExist:
                pass
    return code + postfix

def init_reports(log_to_console=False):
    """
    Initialize any data that should be static here
    """
    from logistics.const import Reports
    # These are annoyingly necessary to live in the DB, currently. 
    # Really this should be app logic, I think.
    for code, name in list(Reports.ALL_REPORTS.items()):
        prod = ProductReportType.objects.get_or_create(code=code)[0]
        if prod.name != name:
            prod.name = name
            prod.save()


def init_supply_point_types():
    from logistics.models import SupplyPointType
    from logistics.util import config
    for code, name in list(config.SupplyPointCodes.ALL.items()):
        spt = SupplyPointType.objects.get_or_create(code=code)[0]
        if spt.name != name:
            spt.name = name
            spt.save()

def init_test_location_and_supplypoints():
    from rapidsms.contrib.locations.models import Location
    hctype, created = SupplyPointType.objects.get_or_create(code="clinic")
    rmstype, created = SupplyPointType.objects.get_or_create(code="hospital")
    location, created = Location.objects.get_or_create(name='Dangme East', 
                                                       code='de')
    gar, created = Location.objects.get_or_create(name='Greater Accra Region', 
                                                  code='gar')
    location.set_parent(gar)
    try:
        country = Location.objects.get(code=settings.COUNTRY)
    except Location.DoesNotExist:
        country, created = Location.objects.get_or_create(code=settings.COUNTRY, 
                                                          name=settings.COUNTRY)
    gar.set_parent(country)
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
    sp = SupplyPoint.objects.all()[0]
    ps, created = ProductStock.objects.get_or_create(product=ov, supply_point=sp, 
                                       manual_monthly_consumption=None, 
                                       use_auto_consumption=False)
    ps, created = ProductStock.objects.get_or_create(product=ml, supply_point=sp, 
                                       manual_monthly_consumption=None, 
                                       use_auto_consumption=False)
