from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _
from logistics.util import config
from logistics.decorators import logistics_contact_required
from logistics.models import SupplyPoint
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from datetime import datetime

class MessageInitiator(KeywordHandler):
    """
    """
    keyword = "test|TEST"

    @logistics_contact_required()
    def help(self):
        self.respond(_(config.Messages.TEST_HANDLER_HELP))

    @logistics_contact_required()
    def handle(self, text):
        result = text.lower().split()
        command = result.pop(0).lower()
        msd_code = result.pop(0).upper()
        extra = ''
        while len(result) > 0:
            extra = extra + ' ' + result.pop(0)

        try:
            sp_target = SupplyPoint.objects.get(code__iexact=msd_code)
        except SupplyPoint.DoesNotExist:
            self.respond(_(config.Messages.TEST_HANDLER_BAD_CODE) % {"code":msd_code})
            return True

        if command in  ["la"]:
            for c in sp_target.active_contact_set:
                c.message(_(config.Messages.LOSS_ADJUST_HELP))
            SupplyPointStatus.objects.create(supply_point=sp_target,
                                             status_type=SupplyPointStatusTypes.LOSS_ADJUSTMENT_FACILITY,
                                             status_value=SupplyPointStatusValues.REMINDER_SENT,
                                             status_date=self.msg.timestamp)
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["soh", "hmk"]:
            raise Exception("This handler command hasn't been implemented yet")
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["fw"]:
            raise Exception("This handler command hasn't been implemented yet")
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["supervision"]:
            raise Exception("This handler command hasn't been implemented yet")
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["si"]:
            raise Exception("This handler command hasn't been implemented yet")
            #facility only - SMS usage
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["randr"]:
            raise Exception("This handler command hasn't been implemented yet")
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["delivery"]:
            raise Exception("This handler command hasn't been implemented yet")
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["latedelivery"]:
            raise Exception("This handler command hasn't been implemented yet")
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["send_inquiry_message"]:
            #sends to all children under a location - website only
            raise Exception("This handler command hasn't been implemented yet")
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
