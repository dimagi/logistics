from logistics_project.apps.ilsgateway.models import ServiceDeliveryPoint, ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType, DeliveryGroup
import ilsgateway.app as ilsgateway_app
from datetime import datetime, timedelta
from rapidsms.tests.scripted import TestScript
from django.core.management.commands.loaddata import Command

class TestReminders (TestScript):
    apps = ([ilsgateway_app.App])
    fixtures = ['location_test_data']

    def setUp(self):
        TestScript.setUp(self)
        
    def testScript(self):
        a = """
           782399299 > help
           782399299 < To register, send register <name> <msd code>. example: register john patel d34002 
           782399299 > register
           782399299 < To register, send register <name> <msd code>. example: register john patel d34002
           782399299 > register ryan msd12345
           782399299 < Sorry, can't find the location with MSD CODE msd12345
           782399299 > register ryan d35404
           782399299 < Thank you for registering at KILAKALADISP, d35404, ryan
           782399299 > language sw
           782399299 < I will speak to you in Swahili.           
           782399299 > help
           782399299 < Welcome to ILSGateway. Available commands are soh, delivered, not delivered, submitted, not submitted
           782399299 > test reminder soh
           782399299 < Please send in your stock on hand information in the format 'soh <product> <amount> <product> <amount>...' 
           782399299 > soh inj 100
           782399299 < Thank you ryan for reporting your stock on hand for KILAKALADISP.  Still missing imp, coc, iud, pop, con.
           782399299 > soh imp 121 coc 334 iud 4 pop 0 con 0
           782399299 < Thank you ryan for reporting your stock on hand for KILAKALADISP!
           782399299 > test
           782399299 < To test a reminder, send "test reminder [remindername]"; valid tests are soh, delivery, randr. Remember to setup your contact details!
           782399299 > test reminder r&r
           782399299 < Sorry I didn't understand. To test a reminder, send "test reminder [remindername]"; valid tests are soh, delivery, randr.
           782399299 > test reminder randr
           782399299 < Have you sent in your R&R form yet for this quarter? Please reply "submitted" or "not submitted"
           782399299 > no
           782399299 < If you haven't submitted your R&R, respond "not submitted". If you haven't received your delivery, respond "not delivered"
           782399299 > no submitted
           782399299 < You have reported that you haven't yet sent in your R&R.
           782399299 > submitted
           782399299 < Thank you ryan for submitting your R and R form for KILAKALADISP
           782399299 > test reminder delivery
           782399299 < Did you receive your delivery yet? Please reply "delivered inj 200 con 300 imp 10 pop 320 coc 232 iud 10" or "not delivered"
           782399299 > delivered
           782399299 < To record a delivery, respond with "delivered product amount product amount..."
           782399299 > delivered 200 con
           782399299 < Thank you ryan for reporting your delivery for KILAKALADISP
           """
        self.runScript(a)
            
    def tearDown(self):
        pass
