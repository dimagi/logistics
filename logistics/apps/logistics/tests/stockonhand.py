from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
import logistics.apps.logistics.app as logistics_app
from logistics.apps.logistics.models import Product, ProductStock, \
    ProductReportsHelper, Facility, SupplyPointType, Location, STOCK_ON_HAND_REPORT_TYPE

class TestStockOnHand (TestScript):
    apps = ([logistics_app.App])

    def setUp(self):
        TestScript.setUp(self)
        location = Location.objects.get(code='de')
        facilitytype = SupplyPointType.objects.get(code='hc')
        rms = Facility.objects.get(code='garms')
        facility, created = Facility.objects.get_or_create(code='dedh',
                                                           name='Dangme East District Hospital',
                                                           location=location, active=True,
                                                           type=facilitytype, supplied_by=rms)
        mc = Product.objects.get(sms_code='mc')
        lf = Product.objects.get(sms_code='lf')
        ProductStock(product=mc, supply_point=facility,
                     monthly_consumption=8).save()
        ProductStock(product=lf, supply_point=facility,
                     monthly_consumption=5).save()
        facility = Facility(code='tf', name='Test Facility',
                       location=location, active=True,
                       type=facilitytype, supplied_by=rms)
        facility.save()
        mc = Product.objects.get(sms_code='mc')
        lf = Product.objects.get(sms_code='lf')
        mg = Product.objects.get(sms_code='mg')
        self.mc_stock = ProductStock(is_active=True, supply_point=facility,
                                    product=mc, monthly_consumption=10)
        self.mc_stock.save()
        self.lf_stock = ProductStock(is_active=True, supply_point=facility,
                                    product=lf, monthly_consumption=10)
        self.lf_stock.save()
        self.mg_stock = ProductStock(is_active=False, supply_point=facility,
                                     product=mg, monthly_consumption=10)
        self.mg_stock.save()


    def testProductReportsHelper(self):
        sdp = Facility()
        m = Message()
        p = ProductReportsHelper(sdp, STOCK_ON_HAND_REPORT_TYPE, m)
        p.add_product_stock('lf',10, save=False)
        p.add_product_stock('mc',30, save=False)
        p.add_product_stock('aa',0, save=False)
        p.add_product_stock('oq',0, save=False)
        self.assertEquals(p.all(), "lf 10, aa 0, oq 0, mc 30")
        self.assertEquals(p.stockouts(), "aa oq")
        my_iter = p._getTokens("ab10cd20")
        self.assertEquals(my_iter.next(),'ab')
        self.assertEquals(my_iter.next(),'10')
        self.assertEquals(my_iter.next(),'cd')
        self.assertEquals(my_iter.next(),'20')

    def testStockOnHand(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 10
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           16176023315 > soh lf 10 mc 20
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           16176023315 > SOH LF 10 MC 20
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock.
           """
        self.runScript(a)

    def testNothing(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 >
           16176023315 < Sorry, I could not understand your message. Please contact your DHIO for help, or visit http://www.ewsghana.com
           16176023315 > soh
           16176023315 < Dear stella, thank you for reporting the commodities you have in stock. 
           """
        self.runScript(a)

    def testStockout(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 0 mc 0
           16176023315 < Dear cynthia, the following items are stocked out: lf mc. Please place an order now.
           """
        self.runScript(a)

    def testLowSupply(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 7 mc 9
           16176023315 < Dear cynthia, the following items need to be reordered: lf mc. Please place an order now.
           """
        self.runScript(a)

    def testSohAndReceipts(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 10 20 mc 20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have. You received lf 20.
           """
        self.runScript(a)

    def testCombined1(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > soh lf 0 mc 1
           super < Dear super, Test Facility is experiencing the following problems: stockouts lf; below reorder level mc
           pharmacist < Dear cynthia, the following items are stocked out: lf. the following items need to be reordered: mc. Please place an order now.
           """
        self.runScript(a)

    def testCombined2(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > mc 0 mg 1
           super < Dear super, Test Facility is experiencing the following problems: stockouts mc; below reorder level mg
           pharmacist < Dear cynthia, the following items are stocked out: mc. the following items need to be reordered: mg. Please place an order now.
           pharmacist > lf 0 mc 1 mg 100
           super < Dear super, Test Facility is experiencing the following problems: stockouts lf; below reorder level mc; overstocked mg
           pharmacist < Dear cynthia, the following items are stocked out: lf. the following items need to be reordered: mc. Please place an order now.
           """
        self.runScript(a)

    def testCombined3(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > soh mc 0 mg 1 ng 300
           super < Dear super, Test Facility is experiencing the following problems: stockouts mc; below reorder level mg
           pharmacist <  Dear cynthia, the following items are stocked out: mc. the following items need to be reordered: mg. Please place an order now. 
           pharmacist > soh mc 0-2 mg 1-1 ng 300-1
           super < Dear super, Test Facility is experiencing the following problems: stockouts mc; below reorder level mg
           pharmacist <  Dear cynthia, the following items are stocked out: mc. the following items need to be reordered: mg. Please place an order now.
           """
        self.runScript(a)

    def testCombined4(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > soh mc 0 mg 1 ng300-4
           super < Dear super, Test Facility is experiencing the following problems: stockouts mc; below reorder level mg
           pharmacist < Dear cynthia, the following items are stocked out: mc. the following items need to be reordered: mg. Please place an order now. 
           """
        self.runScript(a)

    def testCombined5(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > mc 16 lf 16 mg300
           super < Dear super, Test Facility is experiencing the following problems: overstocked mg
           pharmacist < Dear cynthia, the following items are overstocked: mg. The district admin has been informed.
           """
        self.runScript(a)

    def testStringCleaner(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 10-20 mc 20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have. You received lf 20.
           """
        self.runScript(a)

    def testBadCode(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 0 badcode 10
           16176023315 < You reported: lf, but there were errors: Unrecognized commodity codes: badcode. Please contact your DHIO for assistance.
           16176023315 > soh badcode 10
           16176023315 < Unrecognized commodity codes: badcode. Please contact your DHIO for assistance.
           16176023315 > soh lf 10 m20
           16176023315 < You reported: lf, but there were errors: Unrecognized commodity codes: m. Please contact your DHIO for assistance.
           16176023315 > ad50 -0 as65-0 al25-0 qu0-0 sp0-0 rd0-0
           16176023315 < You reported: rd, sp, qu, ad, al, but there were errors: Unrecognized commodity codes: as. Please contact your DHIO for assistance.
           """
        self.runScript(a)

    def FAILSbadcode(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 0 bad_code 10
           16176023315 < You reported: lf, but there were errors: BAD_CODE is/are not part of our commodity codes. Please contact your DHIO for assistance.
           16176023315 > soh bad_code 10
           16176023315 < BAD_CODE is/are not part of our commodity codes. Please contact your DHIO for assistance.
           """
        self.runScript(a)

    def testPunctuation(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 >   soh lf 10 mc 20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have in stock.
           16176023315 > sohlf10mc20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have in stock.
           16176023315 > lf10mc20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have in stock.
           16176023315 > LF10MC 20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have in stock.
           16176023315 > LF10-1MC 20,3
           16176023315 < Dear cynthia, thank you for reporting the commodities you have. You received lf 1, mc 3.
           16176023315 > LF(10), mc (20)
           16176023315 < Dear cynthia, thank you for reporting the commodities you have in stock.
           16176023315 > LF10-mc20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have in stock.
           16176023315 > LF10-mc20-
           16176023315 < Dear cynthia, thank you for reporting the commodities you have in stock.
           16176023315 > LF10-3mc20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have. You received lf 3.
           16176023315 > LF10----3mc20
           16176023315 < Dear cynthia, thank you for reporting the commodities you have. You received lf 3.
           """
        self.runScript(a)

    def tearDown(self):
        TestScript.tearDown(self)
        self.mc_stock.delete()
        self.mg_stock.delete()
        self.lf_stock.delete()
