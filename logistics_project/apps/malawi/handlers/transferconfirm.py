from __future__ import unicode_literals
from datetime import datetime
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.models import ProductReportsHelper , StockTransfer
from logistics.const import Reports
from logistics.decorators import logistics_contact_and_permission_required
from logistics.util import config
from logistics_project.decorators import validate_base_level


class TransferConfirmHandler(KeywordHandler):
    """
    Confirmation of a "give" operation.
    """

    keyword = "confirm"

    def help(self):
        self.handle("")

    @logistics_contact_and_permission_required(config.Operations.CONFIRM_TRANSFER)
    @validate_base_level([config.BaseLevel.HSA, config.BaseLevel.FACILITY])
    def handle(self, text):
        pending = StockTransfer.pending_transfers().filter\
            (receiver=self.msg.logistics_contact.supply_point).all()
        if len(pending) == 0:
            self.respond(config.Messages.NO_PENDING_TRANSFERS)
        else:
            # the easiest way to mark these in the database, 
            # is to make a fake stock report
            # of the pending transfers, considering them as receipts
            stock_report = ProductReportsHelper(self.msg.logistics_contact.supply_point, 
                                                Reports.REC)
            stock_report.newparse(" ".join([p.sms_format() for p in pending]))
            stock_report.save()
            
            # close the pending transfers
            now = datetime.utcnow()
            for p in pending:
                p.confirm(now)

            if self.base_level_is_hsa:
                receiver_name = self.msg.logistics_contact.name
            else:
                receiver_name = self.msg.logistics_contact.supply_point.name

            self.respond(config.Messages.CONFIRM_RESPONSE, 
                         receiver=receiver_name,
                         products=", ".join([p.sms_format() for p in pending]))
