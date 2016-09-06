from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from logistics.models import SupplyPoint, SupplyPointType
from logistics.util import config
from logistics_project.apps.malawi import loader
from rapidsms.contrib.locations.models import LocationType, Location


class Command(BaseCommand):
    help = "Initialize static data for malawi local development"

    def create_location_type(self, name, slug):
        obj, _ = LocationType.objects.get_or_create(slug=slug)
        obj.name = name
        obj.save()
        return obj

    def create_supply_point_type(self, name, code):
        obj, _ = SupplyPointType.objects.get_or_create(code=code)
        obj.name = name
        obj.save()
        return obj

    def get_location_type(self, slug):
        return LocationType.objects.get(slug=slug)

    def get_supply_point_type(self, code):
        return SupplyPointType.objects.get(code=code)

    def create_location(self, type_code, parent=None):
        obj = Location(
            type=self.get_location_type(type_code),
        )

        if parent:
            obj.parent_type = ContentType.objects.get(app_label='locations', model='location')
            obj.parent_id = parent.pk

        obj.save()
        return obj

    def create_supply_point(self, name, type_code, code, location):
        obj = SupplyPoint(
            name=name,
            type=self.get_supply_point_type(type_code),
            code=code,
            location=location
        )

        obj.save()
        return obj

    def handle(self, *args, **options):
        loader.init_static_data(log_to_console=True, do_locations=False, do_products=True)

        self.create_location_type('Country', config.LocationCodes.COUNTRY)
        self.create_location_type('District', config.LocationCodes.DISTRICT)
        self.create_location_type('Facility', config.LocationCodes.FACILITY)
        self.create_location_type('HSA', config.LocationCodes.HSA)

        self.create_supply_point_type('Country', config.SupplyPointCodes.COUNTRY)
        self.create_supply_point_type('District', config.SupplyPointCodes.DISTRICT)
        self.create_supply_point_type('Facility', config.SupplyPointCodes.FACILITY)
        self.create_supply_point_type('HSA', config.SupplyPointCodes.HSA)

        country_loc = self.create_location(config.LocationCodes.COUNTRY)
        country_sp = self.create_supply_point(
            settings.COUNTRY,
            config.SupplyPointCodes.COUNTRY,
            settings.COUNTRY,
            country_loc
        )

        for i in range(1, 4):
            district_loc = self.create_location(config.LocationCodes.DISTRICT, parent=country_loc)
            district_sp = self.create_supply_point(
                'Test District %s' % i,
                config.SupplyPointCodes.DISTRICT,
                'test_district_%s' % i,
                district_loc
            )
