from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _
from logistics.util import config
from logistics.decorators import logistics_contact_required
from logistics.models import SupplyPoint, Product
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
            for c in sp_target.active_contact_set:
                c.message(_(config.Messages.SOH_HELP_MESSAGE))
            SupplyPointStatus.objects.create(supply_point=sp_target,
                                             status_type=SupplyPointStatusTypes.SOH_FACILITY,
                                             status_value=SupplyPointStatusValues.REMINDER_SENT,
                                             status_date=self.msg.timestamp)
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["fw"]:
            for c in sp_target.active_contact_set:
                c.message(' '.join(result))
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["supervision"]:
            for c in sp_target.active_contact_set:
                c.message(_(config.Messages.SUPERVISION_REMINDER))
            SupplyPointStatus.objects.create(supply_point=sp_target,
                                             status_type=SupplyPointStatusTypes.SUPERVISION_FACILITY,
                                             status_value=SupplyPointStatusValues.REMINDER_SENT,
                                             status_date=self.msg.timestamp)
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["si"]:
            pc = result.pop(0)
            try:
                product = Product.objects.get(product_code=pc)
            except Product.DoesNotExist:
                self.respond(_(config.Messages.INVALID_PRODUCT_CODE ) % {"product_code": pc})
                return True
            #facility only - SMS usage
            if sp_target.type.code.lower() == config.SupplyPointCodes.FACILITY:
                for c in sp_target.active_contact_set:
                    c.message(_(config.Messages.STOCK_INQUIRY_MESSAGE) % {"product_name":product.name,
                                                                          "msd_code":product.product_code})
                self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
            else:
                self.respond(_("Can only initiate product inquiry for a single facility via SMS - %(location_name)s is a %(location_type)s") % {"location_name":"changeme",
                                                                                                                                                "location_type":"changeme"})
        if command in  ["randr"]:
            if sp_target.type.code.lower() == config.SupplyPointCodes.DISTRICT:
                for c in sp_target.active_contact_set:
                    c.message(_(config.Messages.SUBMITTED_REMINDER_DISTRICT))
                SupplyPointStatus.objects.create(supply_point=sp_target,
                                                 status_type=SupplyPointStatusTypes.R_AND_R_DISTRICT,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT,
                                                 status_date=self.msg.timestamp)
            elif sp_target.type.code.lower() == config.SupplyPointCodes.FACILITY:
                for c in sp_target.active_contact_set:
                    c.message(_(config.Messages.SUBMITTED_REMINDER_FACILITY))
                SupplyPointStatus.objects.create(supply_point=sp_target,
                                                 status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT,
                                                 status_date=self.msg.timestamp)

            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["delivery"]:
            if sp_target.type.code.lower() == config.SupplyPointCodes.DISTRICT:
                for c in sp_target.active_contact_set:
                    c.message(_(config.Messages.DELIVERY_REMINDER_DISTRICT))
                SupplyPointStatus.objects.create(supply_point=sp_target,
                                                 status_type=SupplyPointStatusTypes.DELIVERY_DISTRICT,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT,
                                                 status_date=self.msg.timestamp)
            elif sp_target.type.code.lower() == config.SupplyPointCodes.FACILITY:
                for c in sp_target.active_contact_set:
                    c.message(_(config.Messages.DELIVERY_REMINDER_FACILITY))
                SupplyPointStatus.objects.create(supply_point=sp_target,
                                                 status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT,
                                                 status_date=self.msg.timestamp)

            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["latedelivery"]:
            #TODO: Query out counts
            for c in sp_target.active_contact_set:
                c.message(_(config.Messages.DELIVERY_LATE_DISTRICT) % {"group_name":"changeme",
                                                                       "group_total":1,
                                                                       "not_responded_count":2,
                                                                       "not_received_count":3})
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))

        if command in  ["send_inquiry_message"]:
            #sends to all children under a location - website only
            raise Exception("This handler command hasn't been implemented yet")
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
