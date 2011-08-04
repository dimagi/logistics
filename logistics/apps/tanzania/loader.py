import os
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point
from logistics.apps.logistics.models import SupplyPoint, SupplyPointType,\
    ProductReportType, ContactRole, Product, ProductType
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config

from logging import info
import logging

def clear_supplypoints():
    Location.objects.all().delete()
    SupplyPoint.objects.all().delete()

def create_location_types():
    types = (
        ("MOHSW", "moh"),
        ("REGION", "reg"),
        ("DISTRICT", "dis"),
        ("FACILITY", "fac")
    )
    count = 0
    for t in types:
        l = LocationType(name=t[0], slug=t[1])
        l.save()
        count += 1
    print "Created %d loc types." % count

def load_regions(path):
    info("Loading regions %s"  % path)
    if not os.path.exists(path):
        raise

    f = open(path, 'r')
    try:
        count = 0
        for line in f.read().splitlines(): #necessary due to different line endings
            
            if "LONGITUDE" in line:
                continue
            id,name,type,lat,long=line.strip().split(',')
            l = Location.objects.get_or_create(
                name=name,
                code=name,
                type=LocationType.objects.get_or_create(name="REGION")[0])
            l[0].save()
            count += 1
    finally:
        f.close()
    print "Processed %d regions"  % count

def load_districts(path):
    info("Loading districts %s"  % path)
    
    f = open(path, 'r')
    try:
        count = 0
        for line in f.read().splitlines(): #necessary due to different line endings
            if "LONGITUDE" in line:
                continue
            id,region,name=line.split(',')[0:3]
            l = Location.objects.get_or_create(
                code=name,
                name=name,
                type=LocationType.objects.get_or_create(name="REGION")[0],
                parent_id=Location.objects.get(name=region).pk
            )
            l[0].save()
            count += 1
    finally:
        f.close()
    print "Processed %d districts"  % count

    
def load_facilities(path):
    info("Loading facilities %s"  % path)

    f = open(path, 'r')
    count = 0
    try:
        for line in f.read().splitlines(): #necessary due to different line endings
            if "LONGITUDE" in line:
                continue

            id,code,region,district,facility,group,longitude,latitude = line.split(',')[0:8]
            parent = Location.objects.get_or_create(name=district.upper())[0]
            point = None
            if longitude and latitude:
                point = Point.objects.get_or_create(longitude=longitude, latitude=latitude)[0]
            if point:
                loc = Location.objects.get_or_create(name=facility,
                                                     code=facility,
                                                     point=point,
                                                     parent_id=parent.pk)[0]
            else:
                loc = Location.objects.get_or_create(name=facility,
                                                     code=facility,
                                                     parent_id=parent.pk)[0]
            s = SupplyPoint.objects.get_or_create(id=id,
                            code=code,
                            type=SupplyPointType.objects.get_or_create(name="facility", code="fac")[0],
                            location=loc
                        )
            s[0].save()
            count += 1
    finally:
        f.close()
    print "Processed %d facilities" % count

def init_static_data():
    clear_supplypoints()
    create_location_types()
    regions = getattr(settings, "STATIC_REGIONS")
    districts = getattr(settings, "STATIC_DISTRICTS")
    facilities = getattr(settings, "STATIC_FACILITIES")
    if regions and facilities and districts:
        load_regions(regions)
        load_districts(districts)
        load_facilities(facilities)
    info("Success!")