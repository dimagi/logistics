from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
import logistics.apps.logistics.app as logistics_app

class TestReceipts (TestScript):
    apps = ([logistics_app.App])

    def setUp(self):
        TestScript.setUp(self)

    def testReceipt(self):
        a = """
           16176023315 > register stella dwdh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme West District Hospital
           16176023315 > rec jd 10
           16176023315 < Thank you, you reported receipts for jd.
           16176023315 > rec jd 10 mc 20
           16176023315 < Thank you, you reported receipts for jd mc.
           """
        self.runScript(a)

