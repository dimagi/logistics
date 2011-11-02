from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from django.utils.translation import ugettext as _
from logistics.util import config
from logistics.decorators import logistics_contact_required
from logistics.models import SupplyPoint, Product
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from datetime import datetime
from logistics_project.apps.tanzania.reminders import reports

def _send_if_connection(c, message, **kwargs):
    if c.default_connection is not None:
        c.message(message, **kwargs)
        
class MessageInitiator(KeywordHandler,TaggingHandler):
    """
    Initiate test messages for trainings.
    """
    
    keyword = "test"

    @logistics_contact_required()
    def help(self):
        self.respond(_(config.Messages.TEST_HANDLER_HELP))

    @logistics_contact_required()
    def handle(self, text):
        result = text.lower().split()
        if len(result) < 2:
            return self.help()
        
        command = result[0]
        rest = " ".join(result[1:])
        
        try:
            sp_target = SupplyPoint.objects.get(code__iexact=rest)
        except SupplyPoint.DoesNotExist:
            # maybe it's a district, get by name
            try:
                sp_target = SupplyPoint.objects.get(name__iexact=rest)
            except SupplyPoint.DoesNotExist:
                # fail
                self.respond_error(_(config.Messages.TEST_HANDLER_BAD_CODE) % {"code":msd_code})
                return True
        
        # target guaranteed to be set by here
        if command in ["la"]:
            for c in sp_target.active_contact_set:
                _send_if_connection(c, _(config.Messages.LOSS_ADJUST_HELP))
            SupplyPointStatus.objects.create(supply_point=sp_target,
                                             status_type=SupplyPointStatusTypes.LOSS_ADJUSTMENT_FACILITY,
                                             status_value=SupplyPointStatusValues.REMINDER_SENT,
                                             status_date=self.msg.timestamp)
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["soh", "hmk"]:
            for c in sp_target.active_contact_set:
                _send_if_connection(c, _(config.Messages.SOH_HELP_MESSAGE))
            SupplyPointStatus.objects.create(supply_point=sp_target,
                                             status_type=SupplyPointStatusTypes.SOH_FACILITY,
                                             status_value=SupplyPointStatusValues.REMINDER_SENT,
                                             status_date=self.msg.timestamp)
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["fw"]:
            for c in sp_target.active_contact_set:
                _send_if_connection(c, ' '.join(result))
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in  ["supervision"]:
            for c in sp_target.active_contact_set:
                _send_if_connection(c, _(config.Messages.SUPERVISION_REMINDER))
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
                self.respond_error(_(config.Messages.INVALID_PRODUCT_CODE ) % {"product_code": pc})
                return True
            #facility only - SMS usage
            if sp_target.type.code.lower() == config.SupplyPointCodes.FACILITY:
                for c in sp_target.active_contact_set:
                    _send_if_connection(c, _(config.Messages.STOCK_INQUIRY_MESSAGE) % {"product_name":product.name,
                                                                          "msd_code":product.product_code})
                self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
            else:
                self.respond_error(_("Can only initiate product inquiry for a single facility via SMS - %(location_name)s is a %(location_type)s") % {"location_name":"changeme",
                                                                                                                                                "location_type":"changeme"})
        if command in ["randr"]:
            if sp_target.type.code.lower() == config.SupplyPointCodes.DISTRICT:
                for c in sp_target.active_contact_set:
                    _send_if_connection(c, _(config.Messages.SUBMITTED_REMINDER_DISTRICT))
                SupplyPointStatus.objects.create(supply_point=sp_target,
                                                 status_type=SupplyPointStatusTypes.R_AND_R_DISTRICT,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT,
                                                 status_date=self.msg.timestamp)
            elif sp_target.type.code.lower() == config.SupplyPointCodes.FACILITY:
                for c in sp_target.active_contact_set:
                    _send_if_connection(c, _(config.Messages.SUBMITTED_REMINDER_FACILITY))
                SupplyPointStatus.objects.create(supply_point=sp_target,
                                                 status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT,
                                                 status_date=self.msg.timestamp)

            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in ["delivery"]:
            if sp_target.type.code.lower() == config.SupplyPointCodes.DISTRICT:
                for c in sp_target.active_contact_set:
                    _send_if_connection(c, _(config.Messages.DELIVERY_REMINDER_DISTRICT))
                SupplyPointStatus.objects.create(supply_point=sp_target,
                                                 status_type=SupplyPointStatusTypes.DELIVERY_DISTRICT,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT,
                                                 status_date=self.msg.timestamp)
            elif sp_target.type.code.lower() == config.SupplyPointCodes.FACILITY:
                for c in sp_target.active_contact_set:
                    _send_if_connection(c, _(config.Messages.DELIVERY_REMINDER_FACILITY))
                SupplyPointStatus.objects.create(supply_point=sp_target,
                                                 status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT,
                                                 status_date=self.msg.timestamp)

            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        if command in ["latedelivery"]:
            #TODO: Query out counts
            for c in sp_target.active_contact_set:
                _send_if_connection(c, _(config.Messages.DELIVERY_LATE_DISTRICT) % {"group_name":"changeme",
                                                                       "group_total":1,
                                                                       "not_responded_count":2,
                                                                       "not_received_count":3})
            self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))

        if command in ["send_inquiry_message"]:
            #sends to all children under a location - website only
            raise Exception("This handler command hasn't been implemented yet")
            
        # these next three only make sense for districts
        if command in ["randr_report"]:
            assert(sp_target.type.code.lower() == config.SupplyPointCodes.DISTRICT)
            for c in sp_target.active_contact_set:
                _send_if_connection(c, config.Messages.REMINDER_MONTHLY_RANDR_SUMMARY, **reports.construct_randr_summary(sp_target))
            self.respond_success()
        if command in ["soh_report"]:
            assert(sp_target.type.code.lower() == config.SupplyPointCodes.DISTRICT)
            for c in sp_target.active_contact_set:
                _send_if_connection(c, config.Messages.REMINDER_MONTHLY_SOH_SUMMARY, **reports.construct_soh_summary(sp_target))
            self.respond_success()
        if command in ["delivery_report"]:
            assert(sp_target.type.code.lower() == config.SupplyPointCodes.DISTRICT)
            for c in sp_target.active_contact_set:
                _send_if_connection(c, config.Messages.REMINDER_MONTHLY_DELIVERY_SUMMARY, **reports.construct_delivery_summary(sp_target))
            self.respond_success()
        if command in ["soh_thank_you"]:
            # test at the facility level for now
            assert(sp_target.type.code.lower() == config.SupplyPointCodes.FACILITY)
            for c in sp_target.active_contact_set:
                _send_if_connection(c, _(config.Messages.SOH_THANK_YOU))
            self.respond_success()

    def respond_success(self):
        self.respond(_(config.Messages.TEST_HANDLER_CONFIRM))
        
        
