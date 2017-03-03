from django.contrib.auth.models import User
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.models import Organization
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from logistics_project.apps.malawi.tests.util import create_hsa
from logistics_project.apps.malawi.util import (hsas_below, hsa_supply_points_below,
    facility_supply_points_below, get_or_create_user_profile, get_visible_districts)
from rapidsms.contrib.locations.models import Location
from static.malawi.config import SupplyPointCodes


class TestMalawiUtils(MalawiTestBase):

    def assert_hsas_below(self, location_code, expected_list):
        result = hsas_below(Location.objects.get(code=location_code))
        self.assertEqual(list(result), expected_list)

    def test_hsas_below(self):
        hsa = create_hsa(self, '+16175551000', 'joe', facility_code='2616')

        # Locations that should have the HSA
        self.assert_hsas_below('261601', [hsa])
        self.assert_hsas_below('2616', [hsa])
        self.assert_hsas_below('26', [hsa])
        self.assert_hsas_below('se', [hsa])
        self.assert_hsas_below('malawi', [hsa])

        # Locations that should not have the HSA
        self.assert_hsas_below('2601', [])
        self.assert_hsas_below('03', [])
        self.assert_hsas_below('sw', [])

    def assert_hsa_supply_points_below(self, location_code, expected_list):
        result = hsa_supply_points_below(Location.objects.get(code=location_code))
        self.assertEqual(list(result), expected_list)

    def test_hsa_supply_points_below(self):
        hsa = create_hsa(self, '+16175551000', 'joe', facility_code='2616')

        # Locations that should have the HSA
        self.assert_hsa_supply_points_below('261601', [hsa.supply_point])
        self.assert_hsa_supply_points_below('2616', [hsa.supply_point])
        self.assert_hsa_supply_points_below('26', [hsa.supply_point])
        self.assert_hsa_supply_points_below('se', [hsa.supply_point])
        self.assert_hsa_supply_points_below('malawi', [hsa.supply_point])

        # Locations that should not have the HSA
        self.assert_hsas_below('2601', [])
        self.assert_hsas_below('03', [])
        self.assert_hsas_below('sw', [])

    def assert_facility_supply_points_below(self, location_code, expected_supply_point_codes):
        result = facility_supply_points_below(Location.objects.get(code=location_code)).order_by('code')
        expected_result = SupplyPoint.objects.filter(code__in=expected_supply_point_codes).order_by('code')
        self.assertEqual(list(result), list(expected_result))

    def test_facility_supply_points_below(self):
        # This test depends on the data loaded from static/malawi/health_centers.csv
        self.assert_facility_supply_points_below('9901', ['9901'])
        self.assert_facility_supply_points_below('99', ['9901', '9902', '9903'])
        self.assert_facility_supply_points_below('sw', ['9901', '9902', '9903'])

        all_facility_codes = SupplyPoint.objects.filter(
            type__code=SupplyPointCodes.FACILITY
        ).values_list('code', flat=True)
        self.assert_facility_supply_points_below('malawi', list(all_facility_codes))

    def assert_get_visible_districts(self, user, expected_codes):
        expected_result = Location.objects.filter(code__in=expected_codes).order_by('code')
        self.assertEqual(get_visible_districts(user), list(expected_result))

    def test_get_visible_districts(self):
        # By default the user has access to no districts
        user = User.objects.create_user('joe', '', 'pass')
        profile = get_or_create_user_profile(user)
        self.assert_get_visible_districts(user, [])

        profile.organization = Organization.objects.create(name='Org')
        profile.save()
        self.assert_get_visible_districts(user, [])

        # Test adding districts to profile.organization
        profile.organization.managed_supply_points.add(SupplyPoint.objects.get(code='03'))
        profile.organization.managed_supply_points.add(SupplyPoint.objects.get(code='26'))
        self.assert_get_visible_districts(user, ['03', '26'])

        # Test setting profile.supply_point to a district
        profile.supply_point = SupplyPoint.objects.get(code='15')
        profile.save()
        self.assert_get_visible_districts(user, ['03', '15', '26'])

        profile.supply_point = SupplyPoint.objects.get(code='03')
        profile.save()
        self.assert_get_visible_districts(user, ['03', '26'])

        profile.organization.managed_supply_points.clear()
        self.assert_get_visible_districts(user, ['03'])

        # Test setting profile.location to a district
        profile.supply_point = None
        profile.location = Location.objects.get(code='26')
        profile.save()
        self.assert_get_visible_districts(user, ['26'])

        # Test setting profile.location to a zone
        profile.location = Location.objects.get(code='no')
        profile.save()
        self.assert_get_visible_districts(user, ['03'])

        # Test setting profile.location to the country
        profile.location = Location.objects.get(code='malawi')
        profile.save()
        all_districts = SupplyPoint.objects.filter(type__code=SupplyPointCodes.DISTRICT).values_list('code', flat=True)
        self.assert_get_visible_districts(user, all_districts.exclude(code='99'))

        # Test superuser
        profile.location = None
        profile.save()
        self.assert_get_visible_districts(user, [])
        user.is_superuser = True
        user.save()
        self.assert_get_visible_districts(user, all_districts)
