from datetime import datetime
from logistics.decorators import logistics_contact_and_permission_required
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics_project.decorators import require_facility
from logistics.util import config
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class RefrigeratorProductsCollectedHandler(KeywordHandler):
    keyword = "rc"

    def help(self):
        self.handle("")

    @logistics_contact_and_permission_required(config.Operations.REPORT_FRIDGE_MALFUNCTION)
    @require_facility
    def handle(self, text):
        supply_point = self.msg.logistics_contact.supply_point
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
