from django.db import transaction
from logistics.models import SupplyPoint
from logistics.util import config
from logistics.decorators import logistics_contact_and_permission_required
from logistics_project.apps.malawi.util import get_hsa, get_facility
from logistics_project.apps.malawi.handlers.abstract.base import RecordResponseHandler
from logistics_project.decorators import validate_base_level_from_supervisor
from rapidsms.models import Contact


class OrderResponseBaseHandler(RecordResponseHandler):
    hsa = None
    
    def handle_custom(self, text):
        raise NotImplemented("This method must be overridden")
    
    @transaction.commit_on_success
    @logistics_contact_and_permission_required(config.Operations.FILL_ORDER)
    @validate_base_level_from_supervisor([config.BaseLevel.HSA, config.BaseLevel.FACILITY])
    def handle(self, text):
        """
        Check some preconditions, based on shared assumptions of these handlers.
        
        Calls handle custom if things go well, otherwise responds directly and 
        doesn't call the subclass method.
        """

        words = text.split(" ")
        supply_point_code = words[0]

        if self.base_level == config.BaseLevel.HSA:
            hsa = get_hsa(hsa_id)
            if not hsa:
                self.respond(config.Messages.UNKNOWN_HSA, hsa_id=supply_point_code)
                return
            self.supply_point = hsa.supply_point
            self.contacts = [hsa]
        else:
            facility = get_facility(supply_point_code)
            if not facility:
                self.respond(config.Messages.UNKNOWN_FACILITY, supply_point_code=supply_point_code)
                return
            self.supply_point = facility
            self.contacts = list(
                Contact.objects.filter(
                    active=True,
                    supply_point=facility,
                    role__code__in=config.Roles.FACILITY_ONLY
                )
            )

        self.handle_custom(text)
