from __future__ import unicode_literals
from rapidsms.models import Contact
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from logistics.models import SupplyPoint

from logistics.util import config


class TestCreateUser(MalawiTestBase):

    def testRegister(self):
        a = """
              +8005551212 > hsa stella 1 2616
              +8005551212 < Sorry, you have to be registered with the system to do that. For help, please contact your supervisor
              +8005551212 > manage manager ic 2616
              +8005551212 < Congratulations manager, you have been registered for the cStock System. Your facility is Ntaja and your role is: in charge
              +8005551212 > hsa stella 1 2616
              +8005551212 < %(confirm)s
            """ % {"confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(a)
        c = Contact.objects.get(name="stella")
        sp = SupplyPoint.objects.get(code="261601")
        self.assertEqual(c.supply_point, sp)
        self.assertEqual(None, c.default_connection)
