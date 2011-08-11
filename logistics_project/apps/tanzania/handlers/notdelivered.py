from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.util import config
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from logistics.decorators import logistics_contact_required

class NotDelivered(KeywordHandler):
    
    keyword = "sijapokea"

    def help(self):
        self.handle(text="")
        
    @logistics_contact_required()
    def handle(self, text):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point

        if sp.type.code.lower() == config.SupplyPointCodes.DISTRICT:
            st = SupplyPointStatusTypes.DELIVERY_DISTRICT
        elif sp.type.code.lower() == config.SupplyPointCodes.FACILITY:
            st = SupplyPointStatusTypes.DELIVERY_FACILITY
        else:
            # TODO be graceful
            raise Exception("bad location type: %s" % sp.type.name)

        SupplyPointStatus.objects.create(status_type=st,
                                         status_value=SupplyPointStatusValues.NOT_RECEIVED,
                                         supply_point=sp)
        self.respond(_(config.Messages.NOT_DELIVERED_CONFIRM))