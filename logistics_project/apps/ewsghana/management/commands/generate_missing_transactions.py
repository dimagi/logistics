import sys
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from dimagi.utils.couch.database import get_db
from logistics_project.apps.ewsghana import loader

class Command(BaseCommand):
    help = "Generate missing transactions from historical product reports"

    def handle(self, *args, **options):
        from logistics.models import ProductReport, StockTransaction, SupplyPoint, Product
        
        txs_created_count = 0
        last_transaction_created = None
        for facility in SupplyPoint.objects.all():
            for product in Product.objects.all():
                prs = ProductReport.objects.filter(supply_point=facility, product=product).order_by('report_date')
                beginning_balance = 0
                last_transaction = None
                generated_transaction = None
                for report in prs:
                    if report.stocktransaction_set.count() > 0:
                        if last_transaction is None:
                            last_transaction = report.stocktransaction_set.all()[0]
                        break
                    st = StockTransaction.from_product_report(report, beginning_balance)
                    if st is not None:
                        if last_transaction is not None:
                            if (st.ending_balance == last_transaction.beginning_balance) or \
                              ((st.ending_balance == last_transaction.ending_balance)):
                                # we generated a transaction where it's not needed
                                break
                            if (st.date - last_transaction.date) > timedelta(minutes=1):
                                print "ERROR: transaction generated in a time period after transactions were activated!!!!"
                                print "  %s %s %s" % (facility, product, report.pk)
                                print "  old tx beg (%s) end (%s) %s" % (last_transaction.beginning_balance, last_transaction.ending_balance, last_transaction.date)
                                print "  new tx beg (%s) end (%s) %s" % (st.beginning_balance, st.ending_balance, st.date)
                                for r in prs:
                                    print "    pr %s quantity(%s) (%s) tx(%s)" % (r.report_date, r.quantity, r.report_type, r.stocktransaction_set.count())
                                sys.exit()
                        st.save()
                        print "Created new transaction (%s)" % st.pk
                        generated_transaction = st
                        txs_created_count = txs_created_count + 1
                        beginning_balance = st.ending_balance
                        if last_transaction_created == None or \
                          last_transaction_created.date < st.date:
                            last_transaction_created = st
                if last_transaction is not None and \
                  generated_transaction is not None and \
                  (generated_transaction.ending_balance != last_transaction.beginning_balance):
                    if generated_transaction.ending_balance == last_transaction.ending_balance:
                        # that transaction wasn't necessary
                        print "DELETING unnecessary transaction (%s)" % last_transaction.pk
                        last_transaction.delete()
                    else:
                        last_transaction.beginning_balance = generated_transaction.ending_balance
                        last_transaction.quantity = last_transaction.ending_balance - last_transaction.beginning_balance
                        last_transaction.save()        
                        print "Modified old transaction (%s)" % last_transaction.pk
                        print "Updating end balance of last transaction to match beginning balance of new transactions"
                        print "  %s, %s" % (facility, product)
                        print "  new tx %s %s %s" % (generated_transaction.beginning_balance, generated_transaction.ending_balance, generated_transaction.date)
                        print "  old tx %s %s %s" % (last_transaction.beginning_balance, last_transaction.ending_balance, last_transaction.date)
        txs_count = StockTransaction.objects.count()
        print "%s transactions generated! new transaction count is %s" % (txs_created_count, txs_count)
        if last_transaction_created is not None:
            print "newest transaction created at %s %s" % (last_transaction_created.date, last_transaction_created.pk)
