from __future__ import print_function
from __future__ import unicode_literals
from builtins import object
import os
import re
from django.db import transaction
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location
from logistics.models import SupplyPoint, SupplyPointType,\
    ProductReportType, ContactRole, Product, ProductType
from logistics.util import config
from logistics_project.loader.base import load_report_types, load_roles
import csv
from pytz import timezone
from datetime import datetime
import pytz
from scheduler.models import EventSchedule
from django.core.exceptions import ObjectDoesNotExist


class LoaderException(Exception):
    pass


def load_static_data_for_tests():
    """
    Load static data to be used for tests. The static data loaded here
    is not kept up to date with the latest database data but is sufficient
    for running tests against.
    """
    load_report_types()
    load_roles()
    load_location_types()
    load_base_locations()
    load_locations_from_path(settings.STATIC_LOCATIONS)
    load_products(settings.STATIC_PRODUCTS, log_to_console=False)


def load_location_types():
    for code, name in list(config.SupplyPointCodes.ALL.items()):
        SupplyPointType.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )

    for code in [
        config.LocationCodes.COUNTRY,
        config.LocationCodes.ZONE,
        config.LocationCodes.DISTRICT,
        config.LocationCodes.FACILITY,
        config.LocationCodes.HSA,
    ]:
        LocationType.objects.get_or_create(
            slug=code,
            defaults={'name': code}
        )


def load_base_locations():
    country_location = Location.objects.create(
        code=settings.COUNTRY,
        name=settings.COUNTRY.title(),
        type_id=config.LocationCodes.COUNTRY
    )

    country_supply_point = SupplyPoint.objects.create(
        code=country_location.code,
        name=country_location.name,
        type_id=config.SupplyPointCodes.COUNTRY,
        location=country_location
    )

    for code, name in (
        ('no', 'Northern'),
        ('ce', 'Central Eastern'),
        ('cw', 'Central Western'),
        ('se', 'South Eastern'),
        ('sw', 'South Western'),
    ):
        zone_location = Location.objects.create(
            code=code,
            name=name,
            type_id=config.LocationCodes.ZONE,
            parent=country_location
        )

        SupplyPoint.objects.create(
            code=zone_location.code,
            name=zone_location.name,
            type_id=config.SupplyPointCodes.ZONE,
            location=zone_location,
            supplied_by=country_supply_point
        )


def load_schedules():
    malawi_tz = timezone("Africa/Blantyre") 
    def _malawi_to_utc(hours):
        localized = malawi_tz.normalize(malawi_tz.localize(datetime(2011, 1, 1, hours, 0)))
        utced = localized.astimezone(pytz.utc)
        return (utced.hour)
    
    def _get_schedule(func):
        try:
            schedule = EventSchedule.objects.get(callback=func)
        except ObjectDoesNotExist:
            schedule = EventSchedule(callback=func)
        schedule.minutes = [0]
        return schedule
    
    warehouse = _get_schedule("warehouse.runner.update_warehouse")
    warehouse.hours = [0, 12]
    warehouse.save()
    
    eo = _get_schedule("logistics_project.apps.malawi.nag.send_district_eo_reminders")
    eo.hours = [_malawi_to_utc(9)]
    eo.days_of_week = [1] # tuesday
    eo.save()
    
    so = _get_schedule("logistics_project.apps.malawi.nag.send_district_so_reminders")
    so.hours = [_malawi_to_utc(9)]
    so.days_of_week = [3] # thursday
    so.save()


def load_products(file_path, log_to_console=True):
    if log_to_console: print("loading static products from %s" % file_path)
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
    
        if log_to_console: print("Successfully processed %s products." % count)
    
    finally:
        csv_file.close()


def load_locations_from_path(path):
    if not os.path.exists(path):
        raise LoaderException("Invalid file path: %s." % path)

    with open(path, 'r') as f:
        FacilityLoader(f).run()


def get_facility_export(file_handle):
    """
    Gets an export of all the facilities in the system as a csv.
    """
    writer = csv.writer(file_handle)
    writer.writerow([
        'Zone Code',
        'Zone Name',
        'District Code',
        'District Name',
        'Facility Code',
        'Facility Name',
    ])

    facilities = SupplyPoint.objects.filter(
        active=True,
        type__code=config.SupplyPointCodes.FACILITY
    ).select_related(
        'supplied_by',
        'supplied_by__supplied_by'
    ).order_by("code")

    for facility in facilities:
        district = facility.supplied_by
        zone = district.supplied_by
        writer.writerow([
            zone.code,
            zone.name,
            district.code,
            district.name,
            facility.code,
            facility.name
        ])


class FacilityLoaderValidationError(Exception):
    validation_msg = None

    def __init__(self, validation_msg):
        super(FacilityLoaderValidationError, self).__init__(validation_msg)
        self.validation_msg = validation_msg


class FacilityLoader(object):
    """
    This utility allows you to create/edit districts and facilities in bulk.
    To use it, pass in a file object and run it. Example:

        with open('filename.csv', 'r') as f:
            FacilityLoader(f).run()

    ** Expected Format **
    The file should be a csv file with 6 columns, in the order below:
        zone code
        zone name
        district code
        district name
        facility code
        facility name

    Using a header is optional, but if a header is used, the columns should have
    the names above.

    ** Facility Usage **
    Facilities are looked up by code. If the facility does not exist, it is
    created. If the facility exists, all of its information is updated.

    ** District Usage **
    Districts are lookuped by code. If the district does not exist, it is
    created. If the district exists, only its zone is updated.

    ** Zone / HSA Usage **
    Zones and HSAs cannot be created or updated with this utility.

    ** Errors **
    If an error occurs, a FacilityLoaderValidationError is raised describing the
    error and the row that had the error. If any exception is raised, no changes
    are applied to the database.
    """

    file_obj = None
    data = None
    valid_zone_codes = None
    district_zone_map = None

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.data = []
        self.valid_zone_codes = list(
            SupplyPoint.objects.filter(type__code=config.SupplyPointCodes.ZONE).values_list('code', flat=True)
        )
        self.district_zone_map = {}

    def validate_column_data(self, line_num, value):
        data = [column.strip() for column in value.split(",")]
        if len(data) != 6:
            raise FacilityLoaderValidationError("Error with row %s. Expected 6 columns of data." % line_num)

        if any([not column for column in data]):
            raise FacilityLoaderValidationError("Error with row %s. Expected a value for every column." % line_num)

        return data

    def validate_zone_code(self, line_num, value):
        if value not in self.valid_zone_codes:
            raise FacilityLoaderValidationError("Error with row %s. Expected zone code to be one of: %s"
                % (line_num, ', '.join(self.valid_zone_codes)))

        return value

    def validate_district_code(self, line_num, value):
        value = value.zfill(2)
        if not re.match(r"^\d\d$", value):
            raise FacilityLoaderValidationError("Error with row %s. Expected district code to consist of "
                "at most 2 digits." % line_num)

        return value

    def validate_facility_code(self, line_num, value):
        value = value.zfill(4)
        if not re.match(r"^\d\d\d\d$", value):
            raise FacilityLoaderValidationError("Error with row %s. Expected facility code to consist of "
                "at most 4 digits." % line_num)

        return value

    def validate_district_zone_mapping(self, line_num, zone_code, district_code):
        if district_code not in self.district_zone_map:
            self.district_zone_map[district_code] = zone_code
        else:
            if self.district_zone_map[district_code] != zone_code:
                raise FacilityLoaderValidationError("Error with row %s. The zone assigned to district %s "
                    "differs across multiple rows. Please check zone for all rows with district %s."
                    % (line_num, district_code, district_code))

    def parse_data(self):
        line_num = 1
        for line in self.file_obj.readlines():
            line = line.decode('utf-8')  # python3 fix

            # Ignore headers
            if line_num == 1 and "district code" in line.lower():
                line_num += 1
                continue

            column_data = self.validate_column_data(line_num, line)
            zone_code, zone_name, district_code, district_name, facility_code, facility_name = column_data

            zone_code = self.validate_zone_code(line_num, zone_code)
            district_code = self.validate_district_code(line_num, district_code)
            facility_code = self.validate_facility_code(line_num, facility_code)

            self.validate_district_zone_mapping(line_num, zone_code, district_code)
            self.data.append({
                'line_num': line_num,
                'zone_code': zone_code,
                'zone_name': column_data[1],
                'district_code': district_code,
                'district_name': column_data[3],
                'facility_code': facility_code,
                'facility_name': column_data[5],
            })

            line_num += 1

    def get_or_create_district_location(self, row, zone_location):
        try:
            district_location = Location.objects.get(code=row['district_code'])
            if district_location.type_id != config.LocationCodes.DISTRICT:
                raise FacilityLoaderValidationError("Error with row %s. District code %s does not reference "
                    "a district." % (row['line_num'], row['district_code']))

            if not district_location.is_active:
                raise FacilityLoaderValidationError("Error with row %s. District code %s references a "
                    "deactivated district." % (row['line_num'], row['district_code']))

            if district_location.parent_id != zone_location.pk:
                district_location.parent = zone_location
                district_location.save()
        except Location.DoesNotExist:
            district_location = Location.objects.create(
                code=row['district_code'],
                name=row['district_name'],
                type_id=config.LocationCodes.DISTRICT,
                parent=zone_location
            )

        return district_location

    def get_or_create_facility_location(self, row, district_location):
        try:
            facility_location = Location.objects.get(code=row['facility_code'])
            if facility_location.type_id != config.LocationCodes.FACILITY:
                raise FacilityLoaderValidationError("Error with row %s. Facility code %s does not reference "
                    "a facility." % (row['line_num'], row['facility_code']))

            if not facility_location.is_active:
                raise FacilityLoaderValidationError("Error with row %s. Facility code %s references a "
                    "deactivated facility." % (row['line_num'], row['facility_code']))
        except Location.DoesNotExist:
            facility_location = Location(code=row['facility_code'])

        facility_location.name = row['facility_name']
        facility_location.type_id = config.LocationCodes.FACILITY
        facility_location.parent = district_location
        facility_location.save()
        return facility_location

    def get_or_create_district_supply_point(self, row, district_location, zone_supply_point):
        try:
            supply_point = SupplyPoint.objects.get(code=district_location.code)
            if supply_point.type_id != config.SupplyPointCodes.DISTRICT:
                raise FacilityLoaderValidationError("Error with row %s. District code %s does not reference "
                    "a district." % (row['line_num'], district_location.code))

            if not supply_point.active:
                raise FacilityLoaderValidationError("Error with row %s. District code %s references a "
                    "deactivated district." % (row['line_num'], district_location.code))

            supply_point.name = district_location.name
            supply_point.location = district_location
            supply_point.supplied_by = zone_supply_point
            supply_point.save()
        except SupplyPoint.DoesNotExist:
            supply_point = SupplyPoint.objects.create(
                code=district_location.code,
                type_id=config.SupplyPointCodes.DISTRICT,
                name=district_location.name,
                location=district_location,
                supplied_by=zone_supply_point
            )

        return supply_point

    def get_or_create_facility_supply_point(self, row, facility_location, district_supply_point):
        try:
            supply_point = SupplyPoint.objects.get(code=facility_location.code)
            if supply_point.type_id != config.SupplyPointCodes.FACILITY:
                raise FacilityLoaderValidationError("Error with row %s. Facility code %s does not reference "
                    "a facility." % (row['line_num'], facility_location.code))

            if not supply_point.active:
                raise FacilityLoaderValidationError("Error with row %s. Facility code %s references a "
                    "deactivated facility." % (row['line_num'], facility_location.code))

            supply_point.name = facility_location.name
            supply_point.location = facility_location
            supply_point.supplied_by = district_supply_point
            supply_point.save()
        except SupplyPoint.DoesNotExist:
            supply_point = SupplyPoint.objects.create(
                code=facility_location.code,
                type_id=config.SupplyPointCodes.FACILITY,
                name=facility_location.name,
                location=facility_location,
                supplied_by=district_supply_point
            )

        return supply_point

    def load_data(self):
        for row in self.data:
            zone_location = Location.objects.get(code=row['zone_code'])
            zone_supply_point = SupplyPoint.objects.get(code=row['zone_code'])
            district_location = self.get_or_create_district_location(row, zone_location)
            facility_location = self.get_or_create_facility_location(row, district_location)
            district_supply_point = self.get_or_create_district_supply_point(row, district_location, zone_supply_point)
            self.get_or_create_facility_supply_point(row, facility_location, district_supply_point)

    def run(self):
        """
        Returns the number of records processed on success, otherwise raises
        a FacilityLoaderValidationError.
        """
        self.parse_data()
        with transaction.atomic():
            self.load_data()

        return len(self.data)


def _clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]
