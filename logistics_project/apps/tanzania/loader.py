import os
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point
from logistics.models import SupplyPoint, SupplyPointType, SupplyPointGroup

from logging import info
from logistics_project.loader.base import load_report_types, load_roles
from logistics.shortcuts import supply_point_from_location
import csv
from dimagi.utils.parsing import string_to_boolean
from logistics_project.apps.tanzania.config import SupplyPointCodes
from scheduler.models import EventSchedule, ALL_VALUE
from django.core.management import call_command
from datetime import datetime
import pytz
from pytz import timezone

from logistics_project.apps.tanzania.reporting.models import OrganizationTree

def clear_supplypoints():
    Location.objects.all().delete()
    SupplyPoint.objects.all().delete()
    Point.objects.all().delete()
    LocationType.objects.all().delete()
    SupplyPointType.objects.all().delete()

def create_location_and_sp_types():
    types = (
        ("MOHSW", SupplyPointCodes.MOH),
        ("REGION", SupplyPointCodes.REGION),
        ("DISTRICT", SupplyPointCodes.DISTRICT),
        ("FACILITY", SupplyPointCodes.FACILITY)
    )
    count = 0
    for t in types:
        LocationType.objects.create(name=t[0], slug=t[1])
        SupplyPointType.objects.create(name=t[0],code=t[1])
        count += 1
    print "Created %d loc types." % count

def _get_code(type, name):
    def clean(string):
        for char in " /\+_":
            string = string.replace(char, "-")
        return string 
    return "%s-%s" % (clean(type), clean(name))

def get_facility_export(file_handle):
    """
    Gets an export of all the facilities in the system as a csv.
    """
    writer = csv.writer(file_handle)
    writer.writerow(['Name', 'Active?', 'MSD Code', 'Parent Name', 
                     'Parent Type', 'Latitude', 'Longitude', 
                     'Group', 'Type'])
    _par_attr = lambda sp, attr: getattr(sp.supplied_by, attr) if sp.supplied_by else ""
    for sp in SupplyPoint.objects.select_related().order_by("code"):
        writer.writerow([sp.name, 
                         sp.active, 
                         sp.code, 
                         sp.supplied_by.name if sp.supplied_by else '', 
                         sp.supplied_by.type.name if sp.supplied_by else '',
                         sp.latitude or "",
                         sp.longitude or "", 
                         sp.groups.all()[0].code if sp.groups.count() else '', 
                         sp.type.name])
    
def load_locations(file):
    count = 0
    messages = []
    reader = csv.reader(file, delimiter=',', quotechar='"')
    for row in reader:
        name, is_active, msd_code, parent_name, parent_type, lat, lon, group, type = row
        
        # strips off headers, if present
        if count == 0 and "msd code" == msd_code.lower():
            continue
        
        # for now assumes these are already create
        try: 
            loc_type = LocationType.objects.get(name__iexact=type)
        except LocationType.DoesNotExist:
            messages.append("Couldn't find type %s (row was ignored)" % (type))
            continue
            
        try:
            parent = Location.objects.get(name__iexact=parent_name,
                                          type__name__iexact=parent_type) \
                            if parent_name and parent_type else None

        except:
            messages.append("Couldn't find parent %s %s (row was ignored)" % (parent_name, parent_type))
            continue

        if lat and lon:
            if Point.objects.filter(longitude=lon, latitude=lat).exists():
                point = Point.objects.filter(longitude=lon, latitude=lat)[0]
            else:
                point = Point.objects.create(longitude=lon, latitude=lat)
        else:
            point = None
        
        code = msd_code if msd_code else _get_code(type, name)
        try:
            l = Location.objects.get(code=code)
        except Location.DoesNotExist:
            l = Location(code=code)
        l.name = name
        l.type = loc_type
        l.is_active = string_to_boolean(is_active)
        if parent: l.parent = parent
        if point:  l.point = point
        l.save()
        
        sp = supply_point_from_location\
                (l, SupplyPointType.objects.get(name__iexact=type),
                 SupplyPoint.objects.get(location=parent) if parent else None)
        
        if group:
            group_obj = SupplyPointGroup.objects.get_or_create(code=group)[0]
            sp.groups.add(group_obj)
            sp.save()
        
        count += 1
    messages.append("Processed %d locations"  % count)
    populate_org_tree()
    return messages

        
def load_locations_from_path(path):
    info("Loading locations %s"  % (path))
    if not os.path.exists(path):
        raise Exception("no file found at %s" % path)

    with open(path, 'r') as f:
        for msg in load_locations(f):
            print msg
        
def populate_org_tree():
    clear_org_tree()
    for s in SupplyPoint.objects.all().order_by('id'):
        if s.supplied_by:
            create_org_tree(s, s.supplied_by)
            print s.name + ' (' + str(s.id) + ')'

def clear_org_tree():
    orgtree = OrganizationTree.objects.all()
    orgtree.delete()

def create_org_tree(below,above):
    if below.type.name=='FACILITY':
        orgtree = OrganizationTree(below=below, above=above, is_facility=True)
    else:
        orgtree = OrganizationTree(below=below, above=above)
    orgtree.save()
    if above.supplied_by:
        create_org_tree(below,above.supplied_by)

def load_fixtures():
    # for the fixtures
    call_command("loaddata", "tz_static")
    
def load_schedules():
    # TODO make this sane.
    # {module: {function: (hours, minutes)}}
    # everything is daily.
    # we convert from TZ time to UTC
    theschedule = {
        "logistics_project.apps.tanzania.reminders.delivery": { 
            "first_facility": (9, 0),
            "second_facility": (9, 0),
            "third_facility": (9, 0),
            "first_district": (9, 0),
            "second_district": (9, 0),
            "third_district": (9, 0)
        },
        "logistics_project.apps.tanzania.reminders.randr": {
            "first_facility": (9, 0),
            "second_facility": (9, 0),
            "third_facility": (9, 0),
            "first_district": (9, 0),
            "second_district": (9, 0),
            "third_district": (9, 0)
        },
        "logistics_project.apps.tanzania.reminders.stockonhand": {
            "first": (9, 0),
            "second": (9, 0),
            "third": (9, 0)
        },
        "logistics_project.apps.tanzania.reminders.stockonhandthankyou": {
            "first": (9, 0)
        },
        "logistics_project.apps.tanzania.reminders.reports": {
            "delivery_summary": (9, 0),
            "soh_summary": (9, 0),
            "randr_summary": (9, 0)
        },
        "logistics_project.apps.tanzania.reminders.test": {
            "test_email_admins": (9, 0)
        },
        "warehouse.runner": {
            "update_warehouse": (0, 0),
            "update_warehouse": (12, 0)
        },
        
    }
                     
    
    tanzania_tz = timezone("Africa/Dar_es_Salaam") 
    def _to_tz_time(hours, minutes):
        localized = tanzania_tz.normalize(tanzania_tz.localize(datetime(2011, 1, 1, hours, minutes)))
        utced = localized.astimezone(pytz.utc)
        return (utced.hour, utced.minute)
    
    for module, funcdict in theschedule.items():
        for func, (hours, minutes) in funcdict.items():
            func_abspath = "%s.%s" % (module, func)
            hours, minutes = _to_tz_time(hours, minutes)
            try:
                schedule = EventSchedule.objects.get(callback=func_abspath)
                schedule.hours = [hours]
                schedule.minutes = [minutes]
            except EventSchedule.DoesNotExist:
                schedule = EventSchedule(callback=func_abspath,
                                         hours=[hours],
                                         minutes=[minutes])
            schedule.save()

def init_static_data():
    clear_supplypoints()
    load_fixtures()
    load_report_types()
    load_roles()
    create_location_and_sp_types()
    load_schedules()
    locations = getattr(settings, "STATIC_LOCATIONS")
    if locations:
        load_locations_from_path(locations)
    info("Success!")