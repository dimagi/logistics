from __future__ import unicode_literals
from datetime import datetime
from logistics.decorators import logistics_contact_and_permission_required
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics_project.decorators import require_facility
from logistics.util import config
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


class RefrigeratorFixedHandler(KeywordHandler):
    keyword = "rf"

    def help(self):
        self.handle("")

    @logistics_contact_and_permission_required(config.Operations.REPORT_FRIDGE_MALFUNCTION)
    @require_facility
    def handle(self, text):
        supply_point = self.msg.logistics_contact.supply_point
        malfunction = RefrigeratorMalfunction.get_open_malfunction(supply_point)
        if not malfunction:
            self.respond(config.Messages.FRIDGE_NOT_REPORTED_BROKEN)
            return

        malfunction.resolved_on = datetime.utcnow()
        malfunction.save()

        self.respond(config.Messages.FRIDGE_FIXED_RESPONSE)
