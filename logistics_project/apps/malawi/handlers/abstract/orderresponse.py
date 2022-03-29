from __future__ import unicode_literals
from django.db import transaction
from logistics.util import config
from logistics.decorators import logistics_contact_and_permission_required
from logistics_project.apps.malawi.util import get_supply_point_and_contacts
from logistics_project.apps.malawi.handlers.abstract.base import RecordResponseHandler
from logistics_project.decorators import validate_base_level_from_supervisor


class OrderResponseBaseHandler(RecordResponseHandler):
    hsa = None
    
    def handle_custom(self, text):
        raise NotImplemented("This method must be overridden")
    
    @transaction.atomic
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
        self.contacts, self.supply_point = get_supply_point_and_contacts(supply_point_code, self.base_level)

        if not self.supply_point:
            if self.base_level_is_hsa:
                self.respond(config.Messages.UNKNOWN_HSA, hsa_id=supply_point_code)
            else:
                self.respond(config.Messages.UNKNOWN_FACILITY, supply_point_code=supply_point_code)
            return

        self.handle_custom(text)
