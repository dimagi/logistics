#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
This script imports facilities into the EWS system from a CSV file of the format
NUMBER, REGION, DISTRICT, FACILITYNAME, TYPE, TOWN, OWNERSHIP

Known bug: this is not unicode friendly

"""

import sys, os
import csv

def LoadFacilities(filename):
    from logistics.apps.logistics.models import Facility, FacilityType, Location
    reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
    errors = 0
    for row in reader:
        region = row[1].strip()
        rms_type = FacilityType.objects.get(code__icontains='rms')
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
            facilitytype = FacilityType.objects.get(name__icontains=type)
        except FacilityType.DoesNotExist:
            print "ERROR: Facility type for %s not found" % type
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
    
def LoadProductsIntoFacilities():
    from logistics.apps.logistics.models import Facility, ProductStock, Product
    facilities = Facility.objects.order_by('type')
    for fac in facilities:
        products = Product.objects.all()
        for product in products:
            if ProductStock.objects.filter(facility=fac, product=product).count() == 0:
                if fac.type == 'RMS':
                    # RMS get all products by default active, 100 stock
                    ProductStock(quantity=0,
                                 facility=fac,
                                 product=product,
                                 monthly_consumption=100).save()
                else:
                    # facilities get all products by default active, 10 stock
                    ProductStock(quantity=0, is_active=False,
                                 facility=fac,
                                 product=product,
                                 monthly_consumption=10).save()
        print "Loaded products into %(fac)s" % {'fac':fac.name}
        
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
try:
    import settings # Assumed to be one directory up
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' " +
                     "in the directory containing ../%r." % __file__)
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv)<2:
        print "usage: import_facilities input_csv_file"
        sys.exit(1)
    filedir = os.path.dirname(__file__)
    sys.path.append(os.path.join(filedir))
    sys.path.append(os.path.join(filedir,'..'))
    sys.path.append(os.path.join(filedir,'..','rapidsms'))
    sys.path.append(os.path.join(filedir,'..','rapidsms','lib'))
    sys.path.append(os.path.join(filedir,'..','rapidsms','lib','rapidsms'))
    sys.path.append(os.path.join(filedir,'..','rapidsms','lib','rapidsms','contrib'))
    LoadFacilities(sys.argv[1])
    LoadProductsIntoFacilities()
