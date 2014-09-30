import re
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes, SupplyPointStatus, SupplyPointStatusValues
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from logistics.decorators import logistics_contact_required
from logistics.util import config
from django.utils.translation import ugettext_noop as _


class Trans(KeywordHandler, TaggingHandler):
    keyword = "trans"

    def help(self):
        self.respond(_(config.Messages.TRANS_HELP))

    @logistics_contact_required()
    def handle(self, text):
        sub_command = text.strip().lower()
        if re.match("hap", sub_command) or re.match("no", sub_command):
            SupplyPointStatus.objects.create\
                (status_type=SupplyPointStatusTypes.TRANS_FACILITY,
                 status_value=SupplyPointStatusValues.NOT_SUBMITTED,
                 supply_point=self.msg.logistics_contact.supply_point,
                 status_date=self.msg.timestamp)
        elif re.match("ndi", sub_command) or re.match("yes", sub_command):
            SupplyPointStatus.objects.create\
                (status_type=SupplyPointStatusTypes.TRANS_FACILITY,
                 status_value=SupplyPointStatusValues.SUBMITTED,
                 supply_point=self.msg.logistics_contact.supply_point,
                 status_date=self.msg.timestamp)

        else:
            self.help()
            return
        self.respond(_(config.Messages.SOH_CONFIRM))