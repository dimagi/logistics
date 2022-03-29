from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from django.core.management.base import LabelCommand, CommandError
from rapidsms.models import Connection, Contact
from logistics.models import ProductStock, ProductReport, StockTransaction,\
    SupplyPoint, StockRequest
import copy
import uuid

class Command(LabelCommand):
    help = "Multiply data"
    args = "multiplier"
    label = "multiplier"

    def handle(self, *args, **options):
        if len(args) < 1: raise CommandError('Please specify %s.' % self.label.split(",")[0])

        multiplier = int(args[0])

        dump_db_state()
        hsas = SupplyPoint.objects.filter(type__code='hsa', active=True)
        count = hsas.count()
        for i, hsa in enumerate(hsas):
            print('processing %s (%s/%s)' % (hsa, i, count))
            multiply_hsa(hsa, multiplier)

        dump_db_state()

def dump_db_state():
    for cls in [SupplyPoint, Contact, Connection, ProductStock,
                ProductReport, StockTransaction, StockRequest]:
        print('there are %s %ss' % (cls.objects.count(), cls.__name__))

def copy_model(model):
    the_copy = copy.copy(model)
    the_copy.pk = None
    return the_copy


def multiply_hsa(sp, count):
    assert sp.type.code == 'hsa'
    for i in range(count - 1):
        # model
        new_hsa = copy_model(sp)
        new_hsa.name = new_hsa.name + " (copy)"
        new_hsa.code = uuid.uuid4().hex
        new_hsa.save()

        # contact (s)
        for contact in sp.contact_set.all():
            new_contact = copy_model(contact)
            new_contact.name = new_contact.name + " (copy)"
            new_contact.supply_point = new_hsa
            new_contact.save()
            for connection in contact.connection_set.all():
                new_conn = copy_model(connection)
                new_conn.contact = new_contact
                new_conn.identity = uuid.uuid4().hex
                new_conn.save()

        # ProductStock
        def _copy_all_sp_models(cls, old, new, extras=lambda x: x):
            obj_map = {}
            for obj in cls.objects.filter(supply_point=old):
                obj_copy = copy_model(obj)
                obj_copy.supply_point = new
                extras(obj_copy)
                obj_copy.save()
                obj_map[obj] = obj_copy

            return obj_map

        _copy_all_sp_models(ProductStock, sp, new_hsa)
        pr_map = _copy_all_sp_models(ProductReport, sp, new_hsa)

        def update_pr(stock_txn):
            if stock_txn.product_report in pr_map:
                stock_txn.product_report = pr_map[stock_txn.product_report]
            else:
                stock_txn.product_report = None
            return stock_txn

        _copy_all_sp_models(StockTransaction, sp, new_hsa, extras=update_pr)
        _copy_all_sp_models(StockRequest, sp, new_hsa)
        # TODO: StockTransfer if necessary

