from rapidsms.tests.scripted import TestScript
from logistics import app as logistics_app
from logistics.models import SupplyPoint, ProductType, Product
from logistics_project.apps.ewsghana.tests.util import load_test_data, \
    report_stock, register_user

class TestReminders (TestScript):
    apps = ([logistics_app.App])
    fixtures = ["ghana_initial_data.json"] 
    def setUp(self):
        TestScript.setUp(self)
        load_test_data()
        self.facility = SupplyPoint.objects.get(code='dedh')
        prod_type = ProductType.objects.all()[0]
        self.commodity, created = Product.objects.get_or_create(
          sms_code='ab', name='Drug A', type=prod_type, units='cycle')
        self.commodity2, created = Product.objects.get_or_create(
          sms_code='cd', name='Drug B', type=prod_type, units='cycle')
        self.contact = register_user(self, '8282', 'tester', self.facility.code, self.facility.name)

    def testReminders(self):
        products_reported, products_not_reported = self.facility.report_status(days_until_late=1)
        self.assertEqual(len(products_reported), 0)
        self.assertEqual(len(products_not_reported), 0)

        self.contact.commodities.add(self.commodity)
        products_reported, products_not_reported = self.facility.report_status(days_until_late=1)
        self.assertEqual(len(products_reported), 0)
        self.assertEqual(products_not_reported[0], self.commodity)
    
        report_stock(self, self.contact, self.commodity, 10)
        products_reported, products_not_reported = self.facility.report_status(days_until_late=1)
        self.assertEqual(products_reported[0], self.commodity)
        self.assertEqual(len(products_not_reported), 0)

        self.contact.commodities.add(self.commodity2)
        products_reported, products_not_reported = self.facility.report_status(days_until_late=1)
        self.assertEqual(products_reported[0], self.commodity)
        self.assertEqual(products_not_reported[0], self.commodity2)
    
        report_stock(self, self.contact, self.commodity2, 10)
        products_reported, products_not_reported = self.facility.report_status(days_until_late=1)
        self.assertTrue(self.commodity in products_reported)
        self.assertTrue(self.commodity2 in products_reported)
        self.assertEqual(len(products_not_reported), 0)
