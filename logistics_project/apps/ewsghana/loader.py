import csv
import random
from rapidsms.conf import settings
from rapidsms.contrib.locations.models import Location
from logistics import loader as logistics_loader
from logistics.util import config

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
    logistics_loader.init_supply_point_types()
    LoadFacilities(facilities_file)
    LoadProductsIntoFacilities(demo)
    init_reminders()

def AddFacilities(filename):
    """ For DELIVER facilities
    
    This function expects a csv file in the format: 
    id, region, district, "facility name", "facility type", x, y, z, etc. 
    """
    from logistics.models import SupplyPoint, SupplyPointType
    from logistics.models import Location

    try:
        country = Location.objects.get(code=settings.COUNTRY)
    except Location.DoesNotExist:
        print "ERROR: COUNTRY specified in settings.py is not a location"
        return
    reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
    errors = 0
    regions = 0
    districts = 0
    facility_locations_count = 0
    rmses = 0
    facilities = 0
    count = 0
    already_exists = 0
    for row in reader:
        #print "line: %s" % count
        count = count + 1
        region_name = row[1].strip()
        district_name = row[2].strip()
        facility_name = row[3].strip()
        region, region_created = _get_or_create_region(region_name, country)
        if region_created:
            regions = regions + 1
        rms, rms_created = _get_or_create_region_rms(region_name, region)
        if rms_created:
            rmses = rmses + 1
        district, district_created = _get_or_create_district(district_name, region)
        if district_created:
            districts = districts + 1
        facility_location, location_created = _get_or_create_location(facility_name, 
                                                                      district, 
                                                                      print_friendly=True)
        if location_created:
            facility_locations_count = facility_locations_count + 1
            #print ("  %s location created" % facility_name.lower())
        facility_code = _generate_code(facility_name)
        facility_type_name = row[4].strip()
        try:
            facility_type = SupplyPointType.objects.get(name__iexact=facility_type_name)
        except SupplyPointType.DoesNotExist:
            print "ERROR: SupplyPoint type for %s not found" % facility_type_name
            errors = errors + 1
            continue
        try:
            SupplyPoint.objects.get(name=facility_name)
        except SupplyPoint.DoesNotExist:
            pass
        else:
            print "  (info: facility %s already exists.)" % facility_name.lower()
            already_exists = already_exists + 1
            continue
        facility, created = SupplyPoint.objects.get_or_create(code=facility_code,
                                                              name=facility_name,
                                                              location=facility_location,
                                                              type=facility_type,
                                                              supplied_by=rms)
        if created:
            facilities = facilities + 1
            print ("  %s created" % facility_name.lower())
            if not location_created:
                print ("  but %s location already existed as %s" % (facility_name, facility_location.name)).lower()
        else:
            print ("%s already exists" % facility_name).lower()
        if facilities != facility_locations_count:
            print "INFO: facility: %s, facilities created:%s, locations created:%s" % \
                (facility_location.name, facilities, facility_locations_count)
        # DELIVER specific
        #_load_DELIVER_products_into_facility(facility, 0, None)
    print "Success!"
    print "There were %s errors" % errors    
    print "%s regions created" % regions
    print "%s rms's created" % rmses
    print "%s districts created" % districts
    print "%s facility locations created" % facility_locations_count
    print "%s facilities created" % facilities
    print "%s facilities already existed" % already_exists
    
def _load_DELIVER_products_into_facility(fac, max_facility_consumption, facility_consumption):
    from logistics.models import Product, ProductStock   
    commodity_codes = ['zt', 'lt', 'ef', 'nv', 'te', 'em', 'zs', 'co', 'fr', 'oq', 'rs']
    for code in commodity_codes:
        product = Product.objects.get(sms_code=code)
        try:
            ps = ProductStock.objects.get(supply_point=fac, product=product)
        except ProductStock.DoesNotExist:
            # no preexisting product stock, which is fine.
            pass
        else:
            print "ProductStock %s for %s already exists!" % (product.name, fac.name)
            continue
        # facilities get all products by default active, 10 stock
        ProductStock(quantity=None, is_active=True, 
                     supply_point=fac,
                     product=product,
                     monthly_consumption=facility_consumption, 
                     use_auto_consumption=False).save()
    print "\tProducts loaded into %s" % fac.name
    
def LoadFacilities(filename):
    """ This function expects a csv file in the format: 
    id, region, district, "facility name", "facility type", x, y, z, etc. 
    
    THIS IS LARGELY DEPRECATED. Use the addFacilities function above for future updates.
    We keep this around for now so as not to break certain book scripts.
    """
    from logistics.models import SupplyPoint, SupplyPointType, Location
    from logistics.util import config
    reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
    errors = 0
    for row in reader:
        region = row[1].strip()
        district = row[2]
        name = row[3].strip()
        rms_type = SupplyPointType.objects.get(code__icontains=config.SupplyPointCodes.REGIONAL_MEDICAL_STORE)
        try:
            rms = SupplyPoint.objects.get(type=rms_type, name__icontains=region)
        except SupplyPoint.DoesNotExist:
            print "ERROR: rms for %s not found" % region
            errors = errors + 1
            continue
        try:
            location = Location.objects.get(name__icontains=district.strip())
        except Location.DoesNotExist:
            print "ERROR: district for %s not found" % district
            errors = errors + 1
            continue
        try:
            print ("%s already exists" % name).lower()
            continue
        except SupplyPoint.DoesNotExist:
            pass
        code = _generate_code(name)
        type = row[4]
        try:
            facilitytype = SupplyPointType.objects.get(name__icontains=type)
        except SupplyPointType.DoesNotExist:
            print "ERROR: SupplyPoint type for %s not found" % type
            errors = errors + 1
            continue
        facility, created = SupplyPoint.objects.get_or_create(code=code,
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
    from logistics.models import SupplyPoint, ProductStock, Product
    facilities = SupplyPoint.objects.order_by('type')
    print facilities.count()
    
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
            try:
                ps = ProductStock.objects.get(supply_point=fac, product=product)
            except ProductStock.DoesNotExist:
                # no preexisting product stock, which is fine.
                pass
            else:
                ps.delete()
            if fac.type.code == config.SupplyPointCodes.REGIONAL_MEDICAL_STORE:
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

def init_reminders():
    from rapidsms.contrib.scheduler.models import EventSchedule, \
        set_weekly_event, set_monthly_event

    # set up first soh reminder
    try:
        EventSchedule.objects.get(callback="logistics.schedule.first_soh_reminder")
    except EventSchedule.DoesNotExist:
        # 2:15 pm on Thursdays
        set_weekly_event("logistics.schedule.first_soh_reminder",3,13,58)
        #EventSchedule.objects.create(callback="logistics.schedule.first_soh_reminder",
        #                             minutes='*')
        
    # set up second soh reminder
    try:
        EventSchedule.objects.get(callback="logistics.schedule.second_soh_reminder")
    except EventSchedule.DoesNotExist:
        # 2:15 pm on Mondays
        set_weekly_event("logistics.schedule.second_soh_reminder",0,13,57)
        #EventSchedule.objects.create(callback="logistics.schedule.second_soh_reminder", 
        #                             minutes='*')

    # set up third soh reminder
    try:
        EventSchedule.objects.get(callback="logistics.schedule.third_soh_to_super")
    except EventSchedule.DoesNotExist:
        # 2:15 pm on Wednesdays
        set_weekly_event("logistics.schedule.third_soh_to_super",2,13,54)
        #EventSchedule.objects.create(callback="logistics.schedule.third_soh_to_super", 
        #                             minutes='*')
        

    # set up rrirv reminder
    try:
        EventSchedule.objects.get(callback="logistics.schedule.reminder_to_submit_RRIRV")
    except EventSchedule.DoesNotExist:
        # 2:15 pm on the 28th
        set_monthly_event("logistics_project.apps.ewsghana.schedule.reminder_to_submit_RRIRV",7,14,15)
        

def _get_or_create_region_rms(region_name, region):
    # DELIVER ONLY
    from logistics.models import SupplyPoint, SupplyPointType
    rms_type = SupplyPointType.objects.get(code=config.SupplyPointCodes.REGIONAL_MEDICAL_STORE)
    created = False
    try:
        rms = SupplyPoint.objects.get(type=rms_type, name__icontains=region_name)
    except SupplyPoint.DoesNotExist:
        rms_name = region_name.strip() + " Regional Medical Store"
        rms = SupplyPoint.objects.create(code=_generate_code(rms_name), 
                                         name=rms_name, 
                                         type=rms_type, 
                                         location=region)
        created = True
        print "RMS for %s not found" % region_name
        # this is the DELIVER-specific part
        _load_DELIVER_products_into_facility(rms, 0, None)
    return rms, created

def _get_or_create_region(region_name, parent):
    from logistics.models import Location
    from rapidsms.contrib.locations.models import LocationType
    created = False
    try:
        region = Location.objects.get(name=region_name)
    except Location.DoesNotExist:
        created = True
        region_type = LocationType.objects.get(slug='region')
        _print_similar_locations(region_name, region_type, parent)
        region_code = _generate_region_code(region_name)
        region = Location.objects.create(name=region_name, 
                                         code=region_code, 
                                         parent=parent, 
                                         type = region_type)
        print "REGION: Created new region %s" % region_name
    return region, created

def _print_similar_locations(name, loc_type, parent):
    try:
        from fuzzywuzzy import process
    except ImportError:
        pass
    else: 
        choices = Location.objects.filter(type=loc_type, parent_id=parent.pk).values_list('name', flat=True)
        if choices:
            closest_match, ratio = process.extractOne(name, choices)
            if ratio > 75:
                print "NOTE: %s is very similar to %s" % (name, closest_match)

def _get_or_create_district(district_name, parent):
    from logistics.models import Location
    from rapidsms.contrib.locations.models import LocationType
    created = False
    try:
        district = Location.objects.get(name=district_name)
    except Location.DoesNotExist:
        created = True
        district_type = LocationType.objects.get(slug='district')
        _print_similar_locations(district_name, district_type, parent)
        district_code = _generate_district_code(district_name)
        district = Location.objects.create(name=district_name, 
                                           code=district_code, 
                                           parent=parent, 
                                           type =district_type)
        print "DISTRICT: Created new district %s" % district_name
    return district, created

def _get_or_create_location(location_name, parent, print_friendly=False):
    from logistics.models import Location
    from rapidsms.contrib.locations.models import LocationType
    created = False
    try:
        location = Location.objects.get(name__iexact=location_name.strip())
    except Location.DoesNotExist:
        created = True
        facility_type = LocationType.objects.get(slug=config.LocationCodes.FACILITY)
        if print_friendly:
            _print_similar_locations(location_name, facility_type, parent)
        location_code = _generate_code(location_name, Location)
        location = Location.objects.create(name=location_name, 
                                           code=location_code, 
                                           parent=parent, 
                                           type =facility_type)
    return location, created

def _generate_code(facility_name, klass=None):
    if klass is None:
        from logistics.models import SupplyPoint
        klass = SupplyPoint
    code = "".join([word[0] for word in facility_name.split()])
    code = code.lower().replace('(','').replace(')','').replace('.','').replace('&','').replace(',','')
    postfix = ''
    try:
        count = 0
        while True:
            klass.objects.get(code=(code + postfix))
            count = count + 1
            postfix = str(count)
    except klass.DoesNotExist:
        pass
    code = code + postfix
    return code

def _generate_district_code(district_name):
    from logistics.models import Location
    #print "DISTRICT %s" % district_name
    code = district_name.split()[0].lower()
    code = code.lower().replace('(','').replace(')','').replace('.','').replace('&','').replace(',','')
    postfix = ''
    try:
        count = 0
        while True:
            Location.objects.get(code=(code + postfix))
            count = count + 1
            postfix = str(count)
    except Location.DoesNotExist:
        pass
    code = code + postfix
    return code

def _generate_region_code(region_name):
    return region_name.lower().replace(' ','_')
    
