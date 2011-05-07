import os
import csv
import random
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point
from logistics.apps.logistics.models import SupplyPoint, SupplyPointType,\
    ProductReportType, ContactRole, Product, ProductType
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config

class LoaderException(Exception):
    pass

def init_static_data(demo=False):
    """
    Initialize any data that should be static here
    """
    if not hasattr(settings, "STATIC_LOCATIONS"):
        print "Please define STATIC_LOCATIONS in your settings.py" + \
              "to a csv list of Facilities."
        return
    facilities_file = getattr(settings, "STATIC_LOCATIONS")
    LoadFacilities(facilities_file)
    LoadProductsIntoFacilities(demo)

def LoadFacilities(filename):
    from logistics.apps.logistics.models import Facility, SupplyPointType, Location
    reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
    errors = 0
    for row in reader:
        region = row[1].strip()
        rms_type = SupplyPointType.objects.get(code__icontains='rms')
        try:
            rms = Facility.objects.get(type=rms_type, name__icontains=region)
        except Facility.DoesNotExist:
            print "ERROR: rms for %s not found" % region
            errors = errors + 1
            continue
        district = row[2]
        try:
            location = Location.objects.get(name__icontains=district.strip())
        except Location.DoesNotExist:
            print "ERROR: district for %s not found" % district
            errors = errors + 1
            continue
        name = row[3].strip()
        code = "".join([word[0] for word in name.split()])
        code = code.lower().replace('(','').replace(')','').replace('.','').replace('&','').replace(',','')
        postfix = ''
        try:
            count = 0
            while True:
                Facility.objects.get(code=(code + postfix))
                count = count + 1
                postfix = str(count)
        except Facility.DoesNotExist:
            pass
        code = code + postfix
        type = row[4]
        try:
            facilitytype = SupplyPointType.objects.get(name__icontains=type)
        except SupplyPointType.DoesNotExist:
            print "ERROR: SupplyPoint type for %s not found" % type
            errors = errors + 1
            continue
        facility, created = Facility.objects.get_or_create(code=code,
                                                           name=name,
                                                           location=location,
                                                           type=facilitytype,
                                                           supplied_by=rms)
        if created:
            print ("%s created" % name).lower()
        else:
            print ("%s already exists" % name).lower()
    print "Success!"
    print "There were %s errors" % errors
    
def LoadProductsIntoFacilities(demo=False):
    from logistics.apps.logistics.models import Facility, ProductStock, Product
    facilities = Facility.objects.order_by('type')
    
    if demo:
        RMS_consumption = 100
        max_RMS_consumption = 330
        facility_consumption = 10
        max_facility_consumption = 33
    else:
        RMS_consumption = None
        max_RMS_consumption = 0
        facility_consumption = None
        max_facility_consumption = 0
    for fac in facilities:
        products = Product.objects.all()
        for product in products:
            if ProductStock.objects.filter(supply_point=fac, product=product).count() == 0:
                if fac.type.code == 'RMS':
                    # RMS get all products by default active, 100 stock
                    ProductStock(quantity=random.randint(0,max_RMS_consumption),
                                 supply_point=fac,
                                 product=product,
                                 monthly_consumption=RMS_consumption).save()
                else:
                    # facilities get all products by default active, 10 stock
                    ProductStock(quantity=random.randint(0,max_facility_consumption), is_active=demo,
                                 supply_point=fac,
                                 product=product,
                                 monthly_consumption=facility_consumption).save()
        print "Loaded products into %(fac)s" % {'fac':fac.name}
