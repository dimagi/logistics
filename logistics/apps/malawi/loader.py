import os
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point

class LoaderException(Exception):
    pass

def load_locations(file_path, log_to_console=True):
    if log_to_console: print "loading static locations from %s" % file_path
    # give django some time to bootstrap itself
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    # clear first
    Location.objects.all().delete()
    LocationType.objects.all().delete()
    
    # create/load static types    
    try:
        country_type = LocationType.objects.get(slug="country")
    except LocationType.DoesNotExist:
        country_type = LocationType.objects.create\
            (slug="country", name="country")
    
    try:
        district_type = LocationType.objects.get(slug="district")
    except LocationType.DoesNotExist:
        district_type = LocationType.objects.create\
            (slug="district", name="district")
    
    try:
        facility_type = LocationType.objects.get(slug="facility", name="facility")
    except LocationType.DoesNotExist:
        facility_type = LocationType.objects.create(slug="facility", name="facility")
    country = Location.objects.create(name=settings.COUNTRY, type=country_type, code=settings.COUNTRY)
    csv_file = open(file_path, 'r')
    try:
        count = 0
        for line in csv_file:
            #leave out first line
            if "district code" in line.lower():
                continue
            district_code, district_name, facility_code, facility_seq, facility_name, hsa_count = line.split(",")
    
            #create/load district
            try:
                district = Location.objects.get(name__iexact=district_name.strip(), type=district_type)
            except Location.DoesNotExist:
                district = Location.objects.create(name=district_name.lower().strip(), type=district_type, 
                                                   code=district_code, parent=country)
            
            #create/load facility
            if not facility_code:
                facility_code = "temp%s" % count
            try:
                facility = Location.objects.get(code=facility_code)
            except Location.DoesNotExist:
                facility = Location(code=facility_code)
            facility.name = facility_name.strip()
            facility.parent = district
            facility.type = facility_type
            facility.save()
            count += 1
    
        if log_to_console: print "Successfully processed %s locations." % count
    
    finally:
        csv_file.close()
            
def _clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]