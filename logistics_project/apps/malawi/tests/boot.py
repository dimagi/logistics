from logistics_project.apps.malawi.tests.register import TestHSARegister
from rapidsms.models import Contact
from logistics_project.apps.malawi.tests.base import MalawiTestBase
__author__ = 'ternus'
from logistics.models import Location, SupplyPoint, ContactRole
from logistics.util import config

class TestBootUser(MalawiTestBase):

    def testBoot(self):
        a = """
              +8005551000 > manage mister manager ic 2616
              +8005551000 < Congratulations mister manager, you have been registered for the cStock System. Your facility is Ntaja and your role is: in charge
              +8005551212 > register albert einstein 2 2616
              +8005551212 < Congratulations albert einstein, you have been registered for the cStock System. Your facility is Ntaja and your role is: hsa
              +8005551212 > boot 261602
              +8005551212 < Sorry, your current role does not allow you to do that. For help, please contact your supervisor
            """
        self.runScript(a)
        c = Contact.objects.get(name="albert einstein")
        sp = SupplyPoint.objects.get(code="261602")
        self.assertEqual(c.supply_point, sp)
        old_name = sp.name
        b = """
              +8005551000 > boot 261602
              +8005551000 < Done. albert einstein has been removed from the cStock system.
        """
        self.runScript(b)

        c = Contact.objects.get(name="albert einstein")
        self.assertFalse(c.is_active)
        self.assertFalse(c.supply_point.is_active)
        self.assertFalse(SupplyPoint.objects.filter(code="261602").exists())
