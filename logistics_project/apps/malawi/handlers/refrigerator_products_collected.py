from datetime import datetime
from logistics_project.apps.malawi.handlers.abstract.base import FacilityUserHandler
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics.util import config


class RefrigeratorProductsCollectedHandler(FacilityUserHandler):
    keyword = "rc"

    def help(self):
        self.handle("")

    def handle(self, text):
        supply_point = self.validate_contact()
        if supply_point:
            malfunction = RefrigeratorMalfunction.get_last_reported_malfunction(supply_point)
            if not malfunction:
                self.respond(config.Messages.FRIDGE_NOT_REPORTED_BROKEN)
                return

            if not malfunction.resolved_on:
                self.respond(config.Messages.FRIDGE_NOT_REPORTED_FIXED)
                return

            if malfunction.products_collected_confirmation_received_on:
                self.respond(config.Messages.FRIDGE_ALREADY_CONFIRMED_COLLECTED)
                return

            malfunction.products_collected_confirmation_received_on = datetime.utcnow()
            malfunction.save()
            self.respond(config.Messages.FRIDGE_CONFIRMATION_RESPONSE)
