import os
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point
from logistics.models import SupplyPoint, SupplyPointType,\
    ProductReportType, ContactRole, Product, ProductType
from logistics.const import Reports
from logistics.util import config
from logistics.shortcuts import supply_point_from_location
from logistics_project.loader.base import load_report_types, load_roles
import csv

class LoaderException(Exception):
    pass

def init_static_data(log_to_console=False, do_locations=False, do_products=True):
    """
    Initialize any data that should be static here
    """
    # These are annoyingly necessary to live in the DB, currently. 
    # Really this should be app logic, I think.
    load_report_types()
    load_roles()
    loc_file = getattr(settings, "STATIC_LOCATIONS")
    if do_locations and loc_file:
        load_locations_from_path(loc_file, log_to_console=log_to_console)
    product_file = getattr(settings, "STATIC_PRODUCTS")
    if do_products and product_file:
        load_products(product_file, log_to_console=log_to_console)
    
    
def clear_locations():
    Location.objects.all().delete()
    LocationType.objects.all().delete()
    
def clear_products():
    Product.objects.all().delete()
    ProductType.objects.all().delete()

def load_products(file_path, log_to_console=True):
    if log_to_console: print "loading static products from %s" % file_path
    # give django some time to bootstrap itself
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    def _int_or_nothing(val):
        try:
            return int(val)
        except ValueError:
            return None
        
    csv_file = open(file_path, 'r')
    try:
        count = 0
        for line in csv_file:
            # leave out first line
            if "product name" in line.lower():
                continue
            #Product Name,Code,Dose,AMC,Family,Formulation,EOP Quantity,# of patients a month,
            name, code, dose, monthly_consumption, typename, form, eop_quant, num_pats, min_pack_size = line.strip().split(",")
            #create/load type
            type = ProductType.objects.get_or_create(name=typename, code=typename.lower())[0]
            
            try:
                product = Product.objects.get(sms_code=code.lower())
            except Product.DoesNotExist:
                product = Product(sms_code=code.lower())
            product.name = name
            product.description = name # todo
            product.type = type
            product.average_monthly_consumption = _int_or_nothing(monthly_consumption)
            product.emergency_order_level = _int_or_nothing(eop_quant)
            product.save()
            
            count += 1
    
        if log_to_console: print "Successfully processed %s products." % count
    
    finally:
        csv_file.close()

def load_locations_from_path(path, log_to_console=True):
    if log_to_console: print("Loading locations %s"  % (path))
    if not os.path.exists(path):
        raise LoaderException("Invalid file path: %s." % path)

    with open(path, 'r') as f:
        msgs = load_locations(f)
        if log_to_console and msgs:
            for msg in msgs:
                print msg

def get_facility_export(file_handle):
    """
    Gets an export of all the facilities in the system as a csv.
    """
    writer = csv.writer(file_handle)
    writer.writerow(['District CODE', 'District', 'CODE', 'Health Center'])
    _par_attr = lambda sp, attr: getattr(sp.supplied_by, attr) if sp.supplied_by else ""
    for sp in SupplyPoint.objects.filter(active=True, 
                                         type__code=config.SupplyPointCodes.FACILITY).order_by("code"):
        writer.writerow([_par_attr(sp, 'code'), 
                         _par_attr(sp, 'name'), 
                         sp.code, 
                         sp.name])
    
def load_locations(file):
    # create/load static types    
    country_type = LocationType.objects.get_or_create(slug=config.LocationCodes.COUNTRY, name=config.LocationCodes.COUNTRY)[0]
    district_type = LocationType.objects.get_or_create(slug=config.LocationCodes.DISTRICT, name=config.LocationCodes.DISTRICT)[0]
    facility_type = LocationType.objects.get_or_create(slug=config.LocationCodes.FACILITY, name=config.LocationCodes.FACILITY)[0]
    hsa_type = LocationType.objects.get_or_create(slug=config.LocationCodes.HSA, name=config.LocationCodes.HSA)[0]
    country = Location.objects.get_or_create(name=settings.COUNTRY[0].upper()+settings.COUNTRY[1:], type=country_type, code=settings.COUNTRY)[0]
    
    country_sp_type = SupplyPointType.objects.get_or_create(name="country", code=config.SupplyPointCodes.COUNTRY)[0]
    country_sp = supply_point_from_location(country, type=country_sp_type)
    district_sp_type = SupplyPointType.objects.get_or_create(name="district", code=config.SupplyPointCodes.DISTRICT)[0]
    fac_sp_type = SupplyPointType.objects.get_or_create(name="health facility", code=config.SupplyPointCodes.FACILITY)[0]
    # we don't use this anywhere in the loader, but make sure to create it
    hsa_sp_type = SupplyPointType.objects.get_or_create(name="health surveillance assistant", code=config.SupplyPointCodes.HSA)[0]
    
    count = 0
    for line in file:
        #leave out first line
        if "district code" in line.lower():
            continue
        district_code, district_name, facility_code, facility_name = \
            [token.strip() for token in line.split(",")]
        
        #create/load district
        def _pad_to(val, target_len):
            if len(val) < target_len:
                val = "%s%s" % ("0" * (len(val) - target_len), val)
            assert len(val) == target_len
            return val 
        
        district_code = _pad_to(district_code, 2)
        facility_code = _pad_to(facility_code, 4)
        
        try:
            district = Location.objects.get(code__iexact=district_code)
        except Location.DoesNotExist:
            district = Location.objects.create(name=district_name.strip(), type=district_type, 
                                               code=district_code, parent=country)
        # create/load district supply point info
        dist_sp = supply_point_from_location(district, type=district_sp_type, parent=country_sp)
        
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
        fac_sp = supply_point_from_location(fac_loc, type=fac_sp_type, parent=dist_sp)
        
        count += 1

    return ["Successfully processed %s locations." % count]

def _clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]