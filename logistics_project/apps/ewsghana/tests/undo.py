from rapidsms.tests.scripted import TestScript
from logistics.models import SupplyPoint
from logistics_project.apps.ewsghana.tests.util import load_test_data, \
    clear_state
from logistics.models import StockTransaction, ProductReport, \
    SupplyPoint, ProductStock

class TestUndo (TestScript):
    def setUp(self):
        TestScript.setUp(self)
        load_test_data()
        clear_state()
        self.facility = SupplyPoint.objects.get(code='dedh')

    def tesNoProductReports(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > undo
           16176023315 < You have not submitted any product reports yet.
           """
        self.runScript(a)

    def testUndoMessages(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh ov 16.0
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           16176023315 > undo
           16176023315 < Success. Your previous report has been removed. It was: soh ov 16.0
           16176023315 > undo
           16176023315 < You have not submitted any product reports yet.
           """
        self.runScript(a)

    def testUndo1Data(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh ov 16.0
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           16176023315 > soh ov 10.0
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           """
        self.runScript(a)
        product_stock = ProductStock.objects.get(supply_point=self.facility, 
                                                 product__sms_code='ov')
        st_count = StockTransaction.objects.all().count()
        pr_count = ProductReport.objects.all().count()
        a = """
           16176023315 > undo
           16176023315 < Success. Your previous report has been removed. It was: soh ov 10.0
           """
        self.runScript(a)
        product_stock = ProductStock.objects.get(supply_point=self.facility, 
                                                 product__sms_code='ov')
        self.assertEqual(product_stock.quantity, 16)
        self.assertEqual(StockTransaction.objects.all().count(), st_count-2)
        self.assertEqual(ProductReport.objects.all().count(), pr_count-2)

    def testUndo2Data(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh ov 16.0 ml 8.0
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           16176023315 > soh ov 10.0 ml 5.0
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           """
        self.runScript(a)
        product_stock = ProductStock.objects.get(supply_point=self.facility, 
                                                 product__sms_code='ml')
        st_count = StockTransaction.objects.all().count()
        pr_count = ProductReport.objects.all().count()
        a = """
           16176023315 > undo
           16176023315 < Success. Your previous report has been removed. It was: soh ov 10.0 ml 5.0
           """
        self.runScript(a)
        product_stock = ProductStock.objects.get(supply_point=self.facility, 
                                                 product__sms_code='ml')
        self.assertEqual(product_stock.quantity, 8)
        self.assertEqual(StockTransaction.objects.all().count(), st_count-4)
        self.assertEqual(ProductReport.objects.all().count(), pr_count-4)
        