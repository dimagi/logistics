from __future__ import unicode_literals
from datetime import datetime, timedelta

import sentry_sdk
from django.utils.translation import gettext as _
from logistics.exceptions import TooMuchStockError
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from logistics.models import ProductReportsHelper, StockRequest, StockTransfer, ProductReport, format_product_string
from logistics.decorators import logistics_contact_and_permission_required
from logistics.const import Reports
from logistics.util import config, ussd_msg_response
from logistics_project.apps.malawi.validators import get_base_level_validator, check_max_levels_malawi
from logistics_project.decorators import validate_base_level
from rapidsms.conf import settings
from rapidsms.contrib.messagelog.models import Message


class ReceiptHandler(KeywordHandler, TaggingHandler):
    """
    Allows SMS reporters to send in "rec jd 10 mc 30" to report 10 jadelle and 30 male condoms received
    """

    keyword = "rec|receipts|received"

    def help(self):
        self.respond(_("Please send in information about your receipts in the format 'rec <product> <amount> <product> <amount>...'"))

    @logistics_contact_and_permission_required(config.Operations.REPORT_RECEIPT)
    @validate_base_level([config.BaseLevel.HSA, config.BaseLevel.FACILITY])
    def handle(self, text):
        dupes = Message.objects.filter(direction="I",
                                       connection=self.msg.connection,
                                       text__iexact=self.msg.raw_text).exclude(pk=self.msg.logger_msg.pk)
        if settings.LOGISTICS_IGNORE_DUPE_RECEIPTS_WITHIN:
            dupe_ignore_threshold = datetime.utcnow() - timedelta(seconds=settings.LOGISTICS_IGNORE_DUPE_RECEIPTS_WITHIN)
            ignore = dupes.filter(date__gte=dupe_ignore_threshold)
            if ignore.count() and ProductReport.objects.filter(message__in=dupes).count():
                self.respond(_("Your receipt message was a duplicate and was discarded."))
                return True

        # at the end of your receipt message you can write:
        # 'from xxx' to indicate the source of the supplies.
        # this is used in the stock transfer workflow
        # TODO: less brittle parsing
        if "from" in text.lower().split():
            splittext = text.lower().split()
            text = " ".join(splittext[:splittext.index("from")])
            supplier = " ".join(splittext[splittext.index("from") + 1:])
        else:
            supplier = None
        
        # parse the report and save as normal receipt
        stock_report = ProductReportsHelper(self.msg.logistics_contact.supply_point,
                                            Reports.REC, self.msg.logger_msg)
        stock_report.newparse(text)

        # Validate base level of products
        try:
            get_base_level_validator(self.base_level)(stock_report)
        except config.BaseLevel.InvalidProductsException as e:
            self.respond(config.Messages.INVALID_PRODUCTS, product_codes=e.product_codes_str)
            return

        # check max stock levels
        try:
            check_max_levels_malawi(stock_report)
        except TooMuchStockError as e:
            # bit of a hack, also check if there was a recent message
            # that matched this and if so force it through
            sentry_sdk.capture_exception(e)
            override_threshold = datetime.utcnow() - timedelta(seconds=60*60*4)
            override = dupes.filter(date__gte=override_threshold)
            if override.count() == 0:
                self.respond(config.Messages.TOO_MUCH_STOCK % {
                    'keyword': self.msg.text.split()[0],
                    'req': e.amount,
                    'prod': e.product,
                    'max': e.max,
                })
                return True

        stock_report.save()

        # Close pending requests. This logic only applies if you are using the
        # StockRequest workflow, but should not break anything if you are not
        StockRequest.close_pending_from_receipt_report(stock_report, self.msg.logistics_contact)
        
        # fill in transfers, if there were any
        if supplier is not None:
            StockTransfer.create_from_receipt_report(stock_report, supplier)
            self.respond(_(config.Messages.RECEIPT_FROM_CONFIRM),
                         products=format_product_string(stock_report.reported_products()),
                         supplier=supplier)
        else:
            self.respond(_(config.Messages.RECEIPT_CONFIRM),
                         products=format_product_string(stock_report.reported_products()))

    def respond(self, template=None, **kwargs):
        self.add_default_tags()
        self.add_tags(kwargs.get("tags", []))
        return ussd_msg_response(self.msg, template, **kwargs)
