from __future__ import absolute_import
from logistics.util import config
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics_project.apps.malawi.tests.util import create_manager
from logistics_project.apps.malawi.tests.base import MalawiTestBase


class RefrigeratorMalfunctionTestCase(MalawiTestBase):

    def testBasicWorkflow(self):
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 0)
        create_manager(self, "5550001", "facility user", role=config.Roles.IN_CHARGE, facility_code='2616')
        create_manager(self, "5550002", "district user", role=config.Roles.DISTRICT_SUPERVISOR, facility_code='26')
        facility = SupplyPoint.objects.get(code='2616')

        self.runScript(
            """5550001 > rm 1
               5550001 < %(facility_response)s
               5550002 < %(district_response)s
            """ % {
                'facility_response':
                    config.Messages.FRIDGE_BROKEN_RESPONSE % {'reason': config.Messages.FRIDGE_BROKEN_NO_GAS},
                'district_response':
                    config.Messages.FRIDGE_BROKEN_NOTIFICATION % {'reason': config.Messages.FRIDGE_BROKEN_NO_GAS, 'facility': '2616'},
            }
        )

        self.assertEqual(RefrigeratorMalfunction.objects.count(), 1)
        malfunction = RefrigeratorMalfunction.get_open_malfunction(facility)
        self.assertTrue(malfunction is not None)
        self.assertEqual(malfunction.supply_point, facility)
        self.assertTrue(malfunction.reported_on is not None)
        self.assertEqual(malfunction.malfunction_reason, RefrigeratorMalfunction.REASON_NO_GAS)
        self.assertTrue(malfunction.responded_on is None)
        self.assertTrue(malfunction.sent_to is None)
        self.assertTrue(malfunction.resolved_on is None)
        self.assertTrue(malfunction.products_collected_confirmation_received_on is None)

        self.runScript(
            """5550002 > transfer 2616 2601
               5550002 < %(district_response)s
               5550001 < %(facility_response)s
            """ % {
                'district_response': config.Messages.TRANSFER_RESPONSE_TO_DISTRICT % {'facility': '2616'},
                'facility_response': config.Messages.TRANSFER_MESSAGE_TO_FACILITY % {'facility': '2601'},
            }
        )

        self.assertEqual(RefrigeratorMalfunction.objects.count(), 1)
        malfunction = RefrigeratorMalfunction.get_open_malfunction(facility)
        self.assertTrue(malfunction is not None)
        self.assertEqual(malfunction.supply_point, facility)
        self.assertTrue(malfunction.reported_on is not None)
        self.assertEqual(malfunction.malfunction_reason, RefrigeratorMalfunction.REASON_NO_GAS)
        self.assertTrue(malfunction.responded_on is not None)
        self.assertEqual(malfunction.sent_to, SupplyPoint.objects.get(code='2601'))
        self.assertTrue(malfunction.resolved_on is None)
        self.assertTrue(malfunction.products_collected_confirmation_received_on is None)

        self.runScript(
            """5550001 > rf
               5550001 < %(facility_response)s
            """ % {
                'facility_response': config.Messages.FRIDGE_CONFIRM_PRODUCTS_COLLECTED_FROM % {'facility': '2601'},
            }
        )

        self.assertEqual(RefrigeratorMalfunction.objects.count(), 1)
        self.assertTrue(RefrigeratorMalfunction.get_open_malfunction(facility) is None)
        malfunction = RefrigeratorMalfunction.get_last_reported_malfunction(facility)
        self.assertTrue(malfunction is not None)
        self.assertEqual(malfunction.supply_point, facility)
        self.assertTrue(malfunction.reported_on is not None)
        self.assertEqual(malfunction.malfunction_reason, RefrigeratorMalfunction.REASON_NO_GAS)
        self.assertTrue(malfunction.responded_on is not None)
        self.assertEqual(malfunction.sent_to, SupplyPoint.objects.get(code='2601'))
        self.assertTrue(malfunction.resolved_on is not None)
        self.assertTrue(malfunction.products_collected_confirmation_received_on is None)

        self.runScript(
            """5550001 > rc
               5550001 < %(facility_response)s
            """ % {
                'facility_response': config.Messages.FRIDGE_CONFIRMATION_RESPONSE,
            }
        )

        self.assertEqual(RefrigeratorMalfunction.objects.count(), 1)
        self.assertTrue(RefrigeratorMalfunction.get_open_malfunction(facility) is None)
        malfunction = RefrigeratorMalfunction.get_last_reported_malfunction(facility)
        self.assertTrue(malfunction is not None)
        self.assertEqual(malfunction.supply_point, facility)
        self.assertTrue(malfunction.reported_on is not None)
        self.assertEqual(malfunction.malfunction_reason, RefrigeratorMalfunction.REASON_NO_GAS)
        self.assertTrue(malfunction.responded_on is not None)
        self.assertEqual(malfunction.sent_to, SupplyPoint.objects.get(code='2601'))
        self.assertTrue(malfunction.resolved_on is not None)
        self.assertTrue(malfunction.products_collected_confirmation_received_on is not None)
