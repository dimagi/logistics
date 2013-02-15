from random import randint, choice, random
from datetime import datetime, timedelta
from django.core.management.base import LabelCommand, CommandError
from rapidsms.models import Connection, Contact
from rapidsms.contrib.messagelog.models import Message
from logistics_project.apps.migration import utils
import sys
from logistics_project.apps.tanzania.migration import check_router
from logistics_project.apps.tanzania.models import DeliveryGroups, SupplyPointStatus, SupplyPointStatusTypes, SupplyPointStatusValues
from logistics_project.apps.tanzania.utils import supply_points_below
from logistics.models import ProductStock, ProductReport, StockTransaction,\
    SupplyPoint, Product

class Command(LabelCommand):
    help = "Generate fake data "
    args = "<start_year>, <submit_chance>"
    label = "start year for data generation, average likelihood of submission per facility"
    

    def handle(self, *args, **options):
        if len(args) < 1: raise CommandError('Please specify %s.' % self.label.split(",")[0])
            
        start_year = int(args[0])
        submit_chance = float(args[1]) if len(args) > 1 else .8
        assert submit_chance > 0, "Submit chance must be a number between 0 and 1"
        assert submit_chance <= 1, "Submit chance must be a number between 0 and 1"
        
        def cleanup():
            Contact.objects.all().delete()
            Connection.objects.all().delete()
            Message.objects.all().delete()
            ProductStock.objects.all().delete()
            ProductReport.objects.all().delete()
            StockTransaction.objects.all().delete()
            SupplyPointStatus.objects.all().delete()

        def generate_contact(fac, date):
            number = "+255%d" % (randint(100000000, 999999999))
            name = "Random Contact %s" % ("".join((choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(5))))
            utils.send_test_message(identity=number,
                                    text="%s %s %s" % ("reg", name, fac.code),
                                    timestamp = str(date))
            utils.send_test_message(identity=number,
                text="language en",
                timestamp = str(date))

        def populate_facility(fac, date):
            print "Populating %s" % fac.name
            for _ in range(randint(0, 5)):
                generate_contact(fac, date)

        def populate_facilities(date):
            print "Populating facilities..."
            for fac in SupplyPoint.objects.filter(type__code='facility'):
                populate_facility(fac, date)

        def _report(fac, date, text):
            if not len(fac.contacts()): return None
            reporter = choice(fac.contacts())
            print "%s > %s reporting %s on %s" % (fac.name, reporter.name, text, date)
            return utils.send_test_message(identity = reporter.phone,
                text = text,
                timestamp = str(date))

        def report_help(fac, date):
            text = choice(("help", "msaada"))
            return _report(fac, date, text)

        def report_soh(fac, date):
            products = [p.sms_code for p in Product.objects.all()]
            reports = []
            for p in products:
                if random() > .95: continue # Chance of not reporting on a product
                quantity = randint(1, 1000)
                reports.append("%s %s" % (p, quantity))
            text = "soh %s" % " ".join(reports)
            return _report(fac, date, text)

        def report_delivery(fac, date):
            if random() > submit_chance:
                return _report(fac, date, "not delivered")
            products = [p.sms_code for p in Product.objects.all()]
            reports = []
            for p in products:
                if random() > .95: continue # Chance of not reporting on a product
                quantity = randint(100, 1000)
                reports.append("%s %s" % (p, quantity))
            text = "delivered %s" % " ".join(reports)
            return _report(fac, date, text)

        def report_la(fac, date):
            products = [p.sms_code for p in Product.objects.all()]
            reports = []
            for p in products:
                if random() < submit_chance: continue # Chance of not reporting on a product
                quantity = randint(-200, 200)
                reports.append("%s %s" % (p, quantity))
            text = "la %s" % " ".join(reports)
            return _report(fac, date, text)

        def report_randr(fac, date):
            text = choice(("submitted", "not submitted"))
            return _report(fac, date, text)

        def report_supervision(fac, date):
            text = "supervision %s" % (choice(("yes", "no")))
            return _report(fac, date, text)

        def bad_report(fac, date):
            text = choice(("supervision", "delivered", "submitted", "soh"))
            bad_text = ("".join((choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(20))))
            return _report(fac, date, "%s %s" % (text, bad_text))

        def report_district_randr(dist, date):
            a = randint(0, len(supply_points_below(dist).filter(groups__code="A")))
            b = randint(0, len(supply_points_below(dist).filter(groups__code="B")))
            c = randint(0, len(supply_points_below(dist).filter(groups__code="C")))
            text = "submitted A %s B %s C %s" % (a,b,c)
            return _report(dist, date, text)

        def report_district_delivery(dist, date):
            return _report(dist, date, choice(("delivered", "not delivered")))

        print "checking router.."
        if not check_router():
            sys.exit()
        print "router running."
        cleanup()
        print "Populating facilities..."
        populate_facilities(datetime(start_year,1,1))

        for c in Contact.objects.all():
            c.language = 'en'
            c.save()

        print "Generating fake data from %s..." % start_year
        dates = map(lambda x: datetime(x[0], x[1], 1), (zip(range(start_year,datetime.now().year + 1) * 12, range(1,13) * 3)))
        print dates
        for date in dates:
            if date > datetime.now(): break
            facs = SupplyPoint.objects.filter(type__code='facility')
            for fac in facs:
                if random() < .1:
                    report_help(fac, date+timedelta(days=randint(0,28), seconds=randint(0, 86400)))
                if random() < .05:
                    bad_report(fac, date+timedelta(days=randint(0,28), seconds=randint(0, 86400)))

            dgs = DeliveryGroups(date.month, facs=facs)

            for fac in facs:
                SupplyPointStatus.objects.create(supply_point=fac,
                    status_type=SupplyPointStatusTypes.SOH_FACILITY,
                    status_value=SupplyPointStatusValues.REMINDER_SENT,
                    status_date=date)
                if random() < submit_chance:
                    report_soh(fac, date)
                SupplyPointStatus.objects.create(supply_point=fac,
                        status_type=SupplyPointStatusTypes.LOSS_ADJUSTMENT_FACILITY,
                        status_value=SupplyPointStatusValues.REMINDER_SENT,
                        status_date=date)
                if random() < submit_chance:
                    report_la(fac, date)

            for fac in dgs.delivering():
                SupplyPointStatus.objects.create(supply_point=fac,
                    status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                    status_value=SupplyPointStatusValues.REMINDER_SENT,
                    status_date=date)
                if random() < submit_chance:
                    report_delivery(fac, date + timedelta(days=randint(1,20), seconds=randint(0, 86400)))

            for fac in dgs.submitting():
                SupplyPointStatus.objects.create(supply_point=fac,
                    status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                    status_value=SupplyPointStatusValues.REMINDER_SENT,
                    status_date=date)
                if random() < submit_chance:
                    report_randr(fac, date + timedelta(days=randint(1,20), seconds=randint(0, 86400)))

                SupplyPointStatus.objects.create(supply_point=fac,
                    status_type=SupplyPointStatusTypes.SUPERVISION_FACILITY,
                    status_value=SupplyPointStatusValues.REMINDER_SENT,
                    status_date=date)
                if random() < submit_chance:
                    report_supervision(fac, date + timedelta(days=randint(0,20), seconds=randint(0, 86400)))

            dists = SupplyPoint.objects.filter(type__code='district')
            for dist in dists:
                SupplyPointStatus.objects.create(supply_point=dist,
                    status_type=SupplyPointStatusTypes.R_AND_R_DISTRICT,
                    status_value=SupplyPointStatusValues.REMINDER_SENT,
                    status_date=date)
                if random() < submit_chance:
                    report_district_randr(dist, date + timedelta(days=randint(0,28), seconds=randint(0, 86400)))

                SupplyPointStatus.objects.create(supply_point=dist,
                        status_type=SupplyPointStatusTypes.DELIVERY_DISTRICT,
                        status_value=SupplyPointStatusValues.REMINDER_SENT,
                        status_date=date)
                if random() < submit_chance:
                    report_district_delivery(dist, date+ timedelta(days=randint(0,28), seconds=randint(0, 86400)))