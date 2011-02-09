from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
import logistics.apps.logistics.app as logistics_app
from logistics.apps.logistics.handlers.stockonhand import ProductStockReport, ServiceDeliveryPoint

class TestStockOnHand (TestScript):
    apps = ([logistics_app.App])

    def setUp(self):
        TestScript.setUp(self)


    def testProductStockReport(self):
        sdp = ServiceDeliveryPoint()
        m = Message()
        p = ProductStockReport(sdp, m)
        p.add_product_stock('jd',10, save=False)
        p.add_product_stock('mc',30, save=False)
        p.add_product_stock('aq',0, save=False)
        p.add_product_stock('al',0, save=False)
        self.assertEquals(p.all(), "jd 10, aq 0, al 0, mc 30")
        self.assertEquals(p.stockouts(), "aq al")

    def testStockOnHand(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, stella
           16176023315 > soh jd 10
           16176023315 < Thank you stella for reporting your stock on hand for Dangme East District Hospital.  Still missing mc.
           16176023315 > soh jd 10 mc 20
           16176023315 < Thank you, you reported you have jd 10, mc 20. If incorrect, please resend.
           """
        self.runScript(a)

    def testStockout(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 > soh jd 0 mc 0
           16176023315 < The following items are stocked out: jd mc. Please place an order now.
           """
        self.runScript(a)

    def testLowSupply(self):
        a = """
           16176023315 > register cynthia dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, cynthia
           16176023315 > soh jd 9 mc 9
           16176023315 < The following items are in low supply: jd mc. Please place an order now.
           """
        self.runScript(a)

