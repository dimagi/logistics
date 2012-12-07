from rapidsms.conf import settings
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact, Connection, Backend
from rapidsms.tests.scripted import TestScript
from logistics.models import Product, ProductStock, \
    ProductReportsHelper, SupplyPoint, SupplyPointType, Location
from logistics.const import Reports
from logistics.util import config
from logistics_project.apps.ewsghana import app as logistics_app

class TestStockOnHand (TestScript):
    apps = ([logistics_app.App])
    fixtures = ["ghana_initial_data.json"] 
    def setUp(self):
        settings.LOGISTICS_STOCKED_BY = 'user'
        TestScript.setUp(self)
        location = Location.objects.get(code='de')
        facilitytype = SupplyPointType.objects.get(code='hc')
        self.rms = SupplyPoint.objects.get(code='garms')
        facility, created = SupplyPoint.objects.get_or_create(code='dedh',
                                                           name='Dangme East District Hospital',
                                                           location=location, active=True,
                                                           type=facilitytype, supplied_by=self.rms)
        assert facility.supplied_by == self.rms
        mc = Product.objects.get(sms_code='mc')
        self.lf = Product.objects.get(sms_code='lf')
        ProductStock(product=mc, supply_point=facility,
                     monthly_consumption=8).save()
        ProductStock(product=self.lf, supply_point=facility,
                     monthly_consumption=5).save()
        facility = SupplyPoint(code='tf', name='Test Facility',
                       location=location, active=True,
                       type=facilitytype, supplied_by=self.rms)
        facility.save()
        mc = Product.objects.get(sms_code='mc')
        mg = Product.objects.get(sms_code='mg')
        self.mc_stock = ProductStock(is_active=True, supply_point=facility,
                                    product=mc, monthly_consumption=10)
        self.mc_stock.save()
        self.lf_stock = ProductStock(is_active=True, supply_point=facility,
                                    product=self.lf, monthly_consumption=10)
        self.lf_stock.save()
        self.mg_stock = ProductStock(is_active=False, supply_point=facility,
                                     product=mg, monthly_consumption=10)
        self.mg_stock.save()

        ng = Product.objects.get(sms_code='ng')
        self.ng_stock = ProductStock(is_active=True, supply_point=facility,
                                    product=ng, monthly_consumption=None)
        self.ng_stock.save()
        
        self.contact = Contact(name='test user')
        self.contact.save()
        self.connection = Connection(backend=Backend.objects.all()[0],
                                     identity="888",
                                     contact=self.contact)
        self.connection.save()
        self.contact.supply_point = facility
        self.contact.save()
        self.contact.commodities.add(ng)
    
    
    def testProductReportsHelper(self):
        sdp = SupplyPoint()
        m = Message()
        p = ProductReportsHelper(sdp, Reports.SOH, m)
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
           16176023315 < To report stock on hand, send SOH [space] [product code] [space] [amount] 
           """
        self.runScript(a)

    def testStockout(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 0 mc 0
           16176023315 < Dear cynthia, these items are stocked out: lf mc. Please order 24 mc, 15 lf.
           """
        self.runScript(a)

    def testStockoutNoConsumption(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh ng 0
           16176023315 < Dear cynthia, these items are stocked out: ng.
           """
        self.runScript(a)

    def testLowSupply(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 7 mc 9
           16176023315 < Dear cynthia, these items need to be reordered: lf mc. Please order 15 mc, 8 lf.
           """
        self.runScript(a)

    def testLowSupplyNoConsumption(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh ng 3
           16176023315 < Dear cynthia, thank you for reporting the commodities you have in stock.
           """
        self.runScript(a)

    def testOverSupply(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > soh lf 30 mc 40
           16176023315 < Dear cynthia, these items are overstocked: lf mc. The district admin has been informed.
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
           super < Dear super, Test Facility is experiencing the following problems: stockouts Lofem; below reorder level Male Condom
           pharmacist < Dear cynthia, these items are stocked out: lf. these items need to be reordered: mc. Please order 29 mc, 30 lf.
           """
        self.runScript(a)

    def testCombined2(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > mc 0 mg 1
           super < Dear super, Test Facility is experiencing the following problems: stockouts Male Condom; below reorder level Micro-G
           pharmacist < Dear cynthia, these items are stocked out: mc. these items need to be reordered: mg. Please order 30 mc, 29 mg.
           pharmacist > mc 0 mg 1 lf 100
           super < Dear super, Test Facility is experiencing the following problems: stockouts Male Condom; below reorder level Micro-G; overstocked Lofem
           pharmacist < Dear cynthia, these items are stocked out: mc. these items need to be reordered: mg. Please order 30 mc, 29 mg.
           """
        self.runScript(a)

    def testCombined3(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > soh mc 0 mg 1 ng 300
           super < Dear super, Test Facility is experiencing the following problems: stockouts Male Condom; below reorder level Micro-G
           pharmacist <  Dear cynthia, these items are stocked out: mc. these items need to be reordered: mg. Please order 30 mc, 29 mg.
           pharmacist > soh mc 0-2 mg 1-1 ng 300-1
           super < Dear super, Test Facility is experiencing the following problems: stockouts Male Condom; below reorder level Micro-G
           pharmacist <  Dear cynthia, these items are stocked out: mc. these items need to be reordered: mg. Please order 30 mc, 29 mg.
           """
        self.runScript(a)

    def testCombined4(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > soh mc 0 mg 1 ng300-4
           super < Dear super, Test Facility is experiencing the following problems: stockouts Male Condom; below reorder level Micro-G
           pharmacist < Dear cynthia, these items are stocked out: mc. these items need to be reordered: mg. Please order 30 mc, 29 mg.
           """
        self.runScript(a)

    def testCombined5(self):
        a = """
           pharmacist > register cynthia tf
           pharmacist < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           super > register super tf incharge
           super < Congratulations super, you have successfully been registered for the Early Warning System. Your facility is Test Facility
           pharmacist > mc 16 lf 16 mg300
           super < Dear super, Test Facility is experiencing the following problems: overstocked Micro-G
           pharmacist < Dear cynthia, these items are overstocked: mg. The district admin has been informed.
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
           16176023315 > lf 0 badcode 10
           16176023315 < You reported: lf, but there were errors: Unrecognized commodity codes: badcode. Please contact your DHIO for assistance.
           16176023315 > badcode 10
           16176023315 < badcode is not a recognized commodity code. Please contact your DHIO for assistance.
           16176023315 > soh lf 10.10 m20
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

    def failTestRMSStockout(self):
        """ This test doesn't pass yet. Something about signals not firing? """
        a = """
           111 > register garep garms
           111 < Congratulations garep, you have successfully been registered for the Early Warning System. Your facility is Greater Accra Regional Medical Store
           222 > register derep dedh
           222 < Congratulations derep, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           111 > soh lf 0
           111 < Dear garep, these items are stocked out: lf.
           222 < Dear derep, Greater Accra Regional Medical Store is STOCKED OUT of: lf
           111 > soh lf 10
           111 < Dear garep, thank you for reporting the commodities you have in stock.
           222 < Dear derep, Greater Accra Regional Medical Store has RESOLVED the following stockouts: lf
           """
        self.runScript(a)

    def tearDown(self):
        TestScript.tearDown(self)
        self.mc_stock.delete()
        self.mg_stock.delete()
        self.lf_stock.delete()
