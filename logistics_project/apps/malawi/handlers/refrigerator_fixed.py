from datetime import datetime
from logistics_project.apps.malawi.handlers.abstract.base import FacilityUserHandler
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics.util import config


class RefrigeratorFixedHandler(FacilityUserHandler):
    keyword = "rf"

    def help(self):
        self.handle("")

    def handle(self, text):
        supply_point = self.validate_contact()
        if supply_point:
            malfunction = RefrigeratorMalfunction.get_open_malfunction(supply_point)
            if not malfunction:
                self.respond(config.Messages.FRIDGE_NOT_REPORTED_BROKEN)
                return

            malfunction.resolved_on = datetime.utcnow()
            malfunction.save()

            if malfunction.sent_to:
                self.respond(config.Messages.FRIDGE_CONFIRM_PRODUCTS_COLLECTED_FROM,
                    facility=malfunction.sent_to.code)
            else:
                self.respond(config.Messages.FRIDGE_CONFIRM_PRODUCTS_COLLECTED)
