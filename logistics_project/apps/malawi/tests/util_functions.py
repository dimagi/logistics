from logistics.models import SupplyPoint
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from logistics_project.apps.malawi.tests.util import create_hsa
from logistics_project.apps.malawi.util import (hsas_below, hsa_supply_points_below,
    facility_supply_points_below)
from rapidsms.contrib.locations.models import Location
from static.malawi.config import SupplyPointCodes


class TestMalawiUtils(MalawiTestBase):

    def assert_hsas_below(self, location_code, expected_list):
        result = hsas_below(Location.objects.get(code=location_code))
        self.assertEqual(list(result), expected_list)

    def test_hsas_below(self):
        hsa = create_hsa(self, '16175551000', 'joe', facility_code='2616')

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
        hsa = create_hsa(self, '16175551000', 'joe', facility_code='2616')

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
