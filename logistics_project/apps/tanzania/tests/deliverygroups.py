from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.models import DeliveryGroups
from rapidsms.models import Contact
from logistics.models import SupplyPoint, SupplyPointGroup
from logistics_project.apps.tanzania.config import SupplyPointCodes

class TestDeliveryGroups(TanzaniaTestScriptBase):

    def setUp(self):
        super(TestDeliveryGroups, self).setUp()
        Contact.objects.all().delete()

    def testDeliveryGroupBasic(self):
        original_submitting = SupplyPoint.objects.filter\
            (type__code=SupplyPointCodes.FACILITY,
             groups__code=DeliveryGroups().current_submitting_group()).count()

        #add another submitting facility
        sp = SupplyPoint.objects.filter\
            (type__code=SupplyPointCodes.FACILITY).exclude\
            (groups__code=DeliveryGroups().current_submitting_group())[0]
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        sp.save()

        new_submitting = SupplyPoint.objects.filter\
            (type__code=SupplyPointCodes.FACILITY,
             groups__code=DeliveryGroups().current_submitting_group()).count()

        self.assertEqual(original_submitting + 1, new_submitting)
