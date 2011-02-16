from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
import logistics.apps.logistics.app as logistics_app

class TestReceipts (TestScript):
    apps = ([logistics_app.App])

    def setUp(self):
        TestScript.setUp(self)

    def testReceipt(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Thank you for registering at Dangme East District Hospital, dedh, stella
           16176023315 > rec jd 10
           16176023315 < Thank you, you reported receipts for jd. If incorrect, please resend.
           16176023315 > rec jd 10 mc 20
           16176023315 < Thank you, you reported receipts for jd mc. If incorrect, please resend.
           """
        self.runScript(a)

