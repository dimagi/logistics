from datetime import datetime, timedelta
from django.db import transaction
from logistics.exceptions import TooMuchStockError
from logistics.util import config
from logistics_project.apps.malawi.handlers.abstract.base import RecordResponseHandler
from logistics.models import StockRequest
from logistics.decorators import logistics_contact_and_permission_required, managed_products_required
from logistics.shortcuts import create_stock_report
from logistics_project.apps.malawi.validators import check_max_levels_malawi
from rapidsms.contrib.messagelog.models import Message


class StockReportBaseHandler(RecordResponseHandler):
    contact = None
    requests = []
    
    def get_report_type(self):
        raise NotImplemented("This method must be overridden")
    
    def send_responses(self):
        raise NotImplemented("This method must be overridden")

    @transaction.commit_on_success
    @logistics_contact_and_permission_required(config.Operations.REPORT_STOCK)
    @managed_products_required()
    def handle(self, text):
        """
        Check some preconditions, based on shared assumptions of these handlers.
        Return true if there is a precondition that wasn't met. If all preconditions
        are met, the variables for facility and name will be set.

        This method will manage some replies as well.
        """
        # at some point we may want more granular permissions for these
        # operations, but for now we just share the one
        self.contact = self.msg.logistics_contact

        try:
            # bit of a hack, also check if there was a recent message
            # that matched this and if so force it through
            cutoff = datetime.utcnow() - timedelta(seconds=60 * 60)
            msgs = Message.objects.filter(direction="I",
                                          connection=self.msg.connection,
                                          text__iexact=self.msg.raw_text,
                                          date__gt=cutoff)
            validation_function = check_max_levels_malawi if msgs.count() <= 1 else None
            stock_report = create_stock_report(
                self.get_report_type(),
                self.contact.supply_point,
                text,
                self.msg.logger_msg,
                additional_validation=validation_function,
            )
            self.requests = StockRequest.create_from_report(stock_report, self.contact)
            self.send_responses(stock_report)
        except TooMuchStockError, e:
            self.respond(config.Messages.TOO_MUCH_STOCK % {
                'keyword': self.msg.text.split()[0],
                'req': e.amount,
                'prod': e.product,
                'max': e.max,
            })
