from __future__ import absolute_import
from datetime import datetime
from logistics.util import config
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics_project.apps.malawi.tests.util import create_manager
from logistics_project.apps.malawi.tests.facility.base import MalawiFacilityLevelTestBase
from rapidsms.models import Contact


class RefrigeratorMalfunctionTestCase(MalawiFacilityLevelTestBase):

    def testBasicWorkflow(self):
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 0)
        create_manager(self, "+5550001", "facility user", role=config.Roles.IN_CHARGE, supply_point_code='2616')
        create_manager(self, "+5550002", "district user", role=config.Roles.DISTRICT_EPI_COORDINATOR, supply_point_code='26')
        facility = SupplyPoint.objects.get(code='2616')

        self.runScript(
            """+5550001 > rm 1
               +5550001 < %(facility_response)s
               +5550002 < %(district_response)s
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

        self.runScript(
            """+5550002 > transfer 2616 2601
               +5550002 < %(district_response)s
               +5550001 < %(facility_response)s
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

        self.runScript(
            """+5550001 > rf
               +5550001 < %(facility_response)s
            """ % {
                'facility_response': config.Messages.FRIDGE_FIXED_RESPONSE,
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

    def testRmValidation(self):
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 0)

        self.runScript(
            """+5550001 > rm 1
               +5550001 < %(response)s
            """ % {
                'response': config.Messages.REGISTRATION_REQUIRED_MESSAGE,
            }
        )
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 0)

        create_manager(self, "+5550001", "facility in charge", role=config.Roles.IN_CHARGE, supply_point_code='2616')
        create_manager(self, "+5550002", "district supervisor", role=config.Roles.DISTRICT_EPI_COORDINATOR, supply_point_code='26')
        create_manager(self, "+5550004", "facility in charge 2", role=config.Roles.IN_CHARGE, supply_point_code='2616')

        in_charge2 = Contact.objects.get(connection__identity='+5550004')
        in_charge2.supply_point = None
        in_charge2.save()

        self.runScript(
            """+5550002 > rm 1
               +5550002 < %(response)s
            """ % {
                'response': config.Messages.UNSUPPORTED_OPERATION,
            }
        )
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 0)

        self.runScript(
            """+5550004 > rm 1
               +5550004 < %(response)s
            """ % {
                'response': config.Messages.ERROR_NO_FACILITY_ASSOCIATION,
            }
        )
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 0)

        self.runScript(
            """+5550001 > rm
               +5550001 < %(response)s
            """ % {
                'response': config.Messages.FRIDGE_HELP,
            }
        )
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 0)

        self.runScript(
            """+5550001 > rm x
               +5550001 < %(response)s
            """ % {
                'response': config.Messages.FRIDGE_HELP_REASON % {'code': 'x'},
            }
        )
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 0)

        self.runScript("+5550001 > rm 2")
        self.assertEqual(RefrigeratorMalfunction.objects.count(), 1)
        malfunction = RefrigeratorMalfunction.objects.all()[0]
        malfunction.reported_on = datetime(2016, 9, 21)
        malfunction.save()

        self.runScript(
            """+5550001 > rm 2
               +5550001 < %(response)s
            """ % {
                'response': config.Messages.FRIDGE_MALFUNCTION_ALREADY_REPORTED % {'date': '21 Sep'},
            }
        )

    def testRfValidation(self):
        create_manager(self, "+5550001", "facility in charge", role=config.Roles.IN_CHARGE, supply_point_code='2616')

        self.runScript(
            """+5550001 > rf
               +5550001 < %(response)s
            """ % {
                'response': config.Messages.FRIDGE_NOT_REPORTED_BROKEN,
            }
        )

        # Test that we still accept rf even though transfer was never received
        self.runScript(
            """+5550001 > rm 3
               +5550001 > rf
               +5550001 < %(response)s
            """ % {
                'response': config.Messages.FRIDGE_FIXED_RESPONSE,
            }
        )

    def testTransferValidation(self):
        create_manager(self, "+5550001", "facility in charge", role=config.Roles.IN_CHARGE, supply_point_code='2616')
        create_manager(self, "+5550002", "district supervisor", role=config.Roles.DISTRICT_EPI_COORDINATOR, supply_point_code='26')
        create_manager(self, "+5550003", "district supervisor 2", role=config.Roles.DISTRICT_EPI_COORDINATOR, supply_point_code='26')
        create_manager(self, "+5550004", "facility in charge 2", role=config.Roles.IN_CHARGE, supply_point_code='2601')

        ds2 = Contact.objects.get(connection__identity='+5550003')
        ds2.supply_point = None
        ds2.save()

        self.runScript(
            """+5550001 > transfer 2616 2601
               +5550001 < %(response)s
            """ % {
                'response': config.Messages.UNSUPPORTED_OPERATION,
            }
        )

        self.runScript(
            """+5550003 > transfer 2616 2601
               +5550003 < %(response)s
            """ % {
                'response': config.Messages.ERROR_NO_DISTRICT_ASSOCIATION,
            }
        )

        self.runScript(
            """+5550002 > transfer
               +5550002 < %(response)s
            """ % {
                'response': config.Messages.FACILITY_TRANSFER_HELP,
            }
        )

        self.runScript(
            """+5550002 > transfer abcd 1234
               +5550002 < %(response)s
            """ % {
                'response': config.Messages.FACILITY_NOT_FOUND % {'facility': 'abcd'},
            }
        )

        self.runScript(
            """+5550002 > transfer 2616 1234
               +5550002 < %(response)s
            """ % {
                'response': config.Messages.FACILITY_NOT_FOUND % {'facility': '1234'},
            }
        )

        self.runScript(
            """+5550002 > transfer 0318 1234
               +5550002 < %(response)s
            """ % {
                'response': config.Messages.FACILITY_NOT_FOUND % {'facility': '0318'},
            }
        )

        self.runScript(
            """+5550002 > transfer 2616 2616
               +5550002 < %(response)s
            """ % {
                'response': config.Messages.FACILITY_MUST_BE_DIFFERENT,
            }
        )

        self.runScript(
            """+5550002 > transfer 2616 2601
               +5550002 < %(response)s
            """ % {
                'response': config.Messages.FRIDGE_NOT_REPORTED_BROKEN_FOR_FACILITY % {'facility': '2616'},
            }
        )

        self.runScript(
            """+5550001 > rm 1
               +5550004 > rm 1
               +5550002 > transfer 2616 2601
               +5550002 < %(response)s
            """ % {
                'response': config.Messages.FRIDGE_REPORTED_BROKEN_FOR_FACILITY % {'facility': '2601'},
            }
        )
