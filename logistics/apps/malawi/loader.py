import os
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point
from logistics.apps.logistics.models import SupplyPoint, SupplyPointType,\
    ProductReportType, ContactRole
from logistics.apps.malawi import const

class LoaderException(Exception):
    pass

def init_static_data():
    """
    Initialize any data that should be static here
    """
    # These are annoyingly necessary to live in the DB. 
    # Really this should be app logic, I think.
    for code, name in const.REPORTS.items():
        prod = ProductReportType.objects.get_or_create(code=code)[0]
        if prod.name != name:
            prod.name = name
            prod.save()
    
    for code, name in const.Roles.ALL_ROLES.items():
        role = ContactRole.objects.get_or_create(code=code)[0]
        if role.name != name:
            role.name = name
            role.save()
    
def clear_locations():
    Location.objects.all().delete()
    LocationType.objects.all().delete()
    
    
def load_locations(file_path, log_to_console=True):
    if log_to_console: print "loading static locations from %s" % file_path
    # give django some time to bootstrap itself
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    # create/load static types    
    country_type = LocationType.objects.get_or_create(slug="country", name="country")[0]
    district_type = LocationType.objects.get_or_create(slug="district", name="district")[0]
    facility_type = LocationType.objects.get_or_create(slug="facility", name="facility")[0]
    hsa_type = LocationType.objects.get_or_create(slug="hsa", name="hsa")[0]
    country = Location.objects.get_or_create(name=settings.COUNTRY, type=country_type, code=settings.COUNTRY)[0]
    
    fac_sp_type = SupplyPointType.objects.get_or_create(name="health facility", code="hf")[0]
    # we don't use this anywhere in the loader, but make sure to create it
    hsa_sp_type = SupplyPointType.objects.get_or_create(name="health surveillance assistant", code="hsa")[0]
    
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
                district = Location.objects.get(code=district_code)
            except Location.DoesNotExist:
                district = Location.objects.create(name=district_name.strip(), type=district_type, 
                                                   code=district_code, parent=country)
            
            #create/load location info
            if not facility_code:
                facility_code = "temp%s" % count
            try:
                fac_loc = Location.objects.get(code=facility_code)
            except Location.DoesNotExist:
                fac_loc = Location(code=facility_code)
            fac_loc.name = facility_name.strip()
            fac_loc.parent = district
            fac_loc.type = facility_type
            fac_loc.save()
            
            # create/load supply point info
            try:
                fac_sp = SupplyPoint.objects.get(location=fac_loc, type=fac_sp_type)
            except SupplyPoint.DoesNotExist:
                fac_sp = SupplyPoint(location=fac_loc)
            fac_sp.name = fac_loc.name
            fac_sp.active = True
            fac_sp.type = fac_sp_type
            fac_sp.code = facility_code
            # TODO
            # fac_sp.supplied_by = ?
            fac_sp.save()
            
            count += 1
    
        if log_to_console: print "Successfully processed %s locations." % count
    
    finally:
        csv_file.close()
            
def _clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]