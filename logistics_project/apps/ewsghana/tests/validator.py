from rapidsms.tests.scripted import TestScript
from logistics.models import SupplyPoint
from logistics_project.apps.ewsghana.tests.util import load_test_data
from logistics_project.apps.ewsghana import app as logistics_app

class TestValidator (TestScript):
    def setUp(self):
        TestScript.setUp(self)
        load_test_data()
        self.facility = SupplyPoint.objects.get(code='dedh')

    def testValidator(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh ov 16
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           """
        self.runScript(a)
        validator = logistics_app.SohAndReceiptValidator()
        # increase in soh w/o receipt
        self.assertRaises(ValueError, 
                          validator.validate, 
                          self.facility, product_stock={'ov':18})
        # increase in soh w/o receipt too small
        self.assertRaises(ValueError, 
                          validator.validate, 
                          self.facility, product_stock={'ov':18}, 
                           product_received={'ov':1})
        # increase in soh w matching receipt
        validator.validate(self.facility, product_stock={'ov':18}, 
                           product_received={'ov':2})
        # increase in soh w over receipt
        validator.validate(self.facility, product_stock={'ov':18}, 
                           product_received={'ov':4})
        # same soh w receipt
        validator.validate(self.facility, product_stock={'ov':16}, 
                           product_received={'ov':10})
        # decrease in soh w receipt
        validator.validate(self.facility, product_stock={'ov':14}, 
                           product_received={'ov':10})        

    def testSMSValidation(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh ov 16
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           16176023315 > soh ov 18
           16176023315 < You reported an increase in ov without an associated receipt. Pls report receipt in the format "[code] [stock on hand] [amount received]"
           16176023315 > soh ov 18 2
           16176023315 < Dear stella, thank you for reporting the commodities you have. You received ov 2.
           16176023315 > soh ov 20 ml 2
           16176023315 < You reported an increase in ov without an associated receipt. Pls report receipt in the format "[code] [stock on hand] [amount received]"
           """
        self.runScript(a)

