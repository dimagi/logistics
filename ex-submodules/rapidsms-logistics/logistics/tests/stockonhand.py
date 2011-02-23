from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
import logistics.apps.logistics.app as logistics_app
from logistics.apps.logistics.models import ProductStockReport, Location, STOCK_ON_HAND_REPORT_TYPE

class TestStockOnHand (TestScript):
    apps = ([logistics_app.App])

    def setUp(self):
        TestScript.setUp(self)


    def testProductStockReport(self):
        sdp = Location()
        m = Message()
        p = ProductStockReport(sdp, STOCK_ON_HAND_REPORT_TYPE, m)
        p.add_product_stock('lf',10, save=False)
        p.add_product_stock('mc',30, save=False)
        p.add_product_stock('aq',0, save=False)
        p.add_product_stock('oq',0, save=False)
        self.assertEquals(p.all(), "lf 10, aq 0, oq 0, mc 30")
        self.assertEquals(p.stockouts(), "aq oq")
        my_iter = p._getTokens("ab10cd20")
        self.assertEquals(my_iter.next(),'ab')
        self.assertEquals(my_iter.next(),'10')
        self.assertEquals(my_iter.next(),'cd')
        self.assertEquals(my_iter.next(),'20')

    def testStockOnHand(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, stella
           16176023315 > soh lf 10
           16176023315 < Thank you stella for reporting your stock on hand for Dangme East District Hospital.  Still missing mc.
           16176023315 > soh lf 10 mc 20
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           16176023315 > SOH LF 10 MC 20
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           """
        self.runScript(a)

    def testStockout(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 > soh lf 0 mc 0
           16176023315 < The following items are stocked out: lf mc. Please place an order now.
           """
        self.runScript(a)

    def testLowSupply(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 > soh lf 9 mc 9
           16176023315 < The following items are in low supply: lf mc. Please place an order now.
           """
        self.runScript(a)

    def testSohAndReceipts(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 > soh lf 10 20 mc 20
           16176023315 < Thank you, you reported you have lf 10, mc 20. You received lf 20. If incorrect, please resend.
           """
        self.runScript(a)

    def testStringCleaner(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 > soh lf 10-20 mc 20
           16176023315 < Thank you, you reported you have lf 10, mc 20. You received lf 20. If incorrect, please resend.
           """
        self.runScript(a)

    def testBadCode(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 > soh lf 0 badcode 10
           16176023315 < You reported: lf, but there were errors: Sorry, invalid product code BADCODE
           16176023315 > soh badcode 10
           16176023315 < Sorry, invalid product code BADCODE
           """
        self.runScript(a)

    def FAILSbadcode(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 > soh lf 0 bad_code 10
           16176023315 < You reported: lf, but there were errors: Sorry, invalid product code BAD_CODE
           16176023315 > soh bad_code 10
           16176023315 < Sorry, invalid product code BAD_CODE
           """
        self.runScript(a)

    def testPunctuation(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 >   soh lf 10 mc 20
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           16176023315 > sohlf10mc20
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           16176023315 > lf10mc20
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           16176023315 > LF10MC 20
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           16176023315 > LF10-1MC 20,3
           16176023315 < Thank you, you reported you have lf 10, mc 20. You received lf 1, mc 3. If incorrect, please resend.
           16176023315 > LF(10), mc (20)
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           16176023315 > LF10-mc20
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           16176023315 > LF10-mc20-
           16176023315 < Thank you, you reported you have lf 10, mc 20. If incorrect, please resend.
           16176023315 > LF10-3mc20
           16176023315 < Thank you, you reported you have lf 10, mc 20. You received lf 3. If incorrect, please resend.
           16176023315 > LF10----3mc20
           16176023315 < Thank you, you reported you have lf 10, mc 20. You received lf 3. If incorrect, please resend.
           """
        self.runScript(a)

