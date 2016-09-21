from datetime import datetime
from logistics.decorators import logistics_contact_and_permission_required
from logistics.models import ContactRole
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics_project.decorators import require_facility
from logistics.util import config
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact


class RefrigeratorMalfunctionHandler(KeywordHandler):
    keyword = "rm"

    def help(self):
        self.handle("")

    def is_text_valid(self, words):
        if len(words) == 0:
            self.respond(config.Messages.FRIDGE_HELP)
            return False

        if words[0] not in RefrigeratorMalfunction.REASONS:
            self.respond(config.Messages.FRIDGE_HELP_REASON, code=words[0])
            return False

        return True

    def get_reason_desc(self, reason):
        return {
            RefrigeratorMalfunction.REASON_NO_GAS: config.Messages.FRIDGE_BROKEN_NO_GAS,
            RefrigeratorMalfunction.REASON_POWER_FAILURE: config.Messages.FRIDGE_BROKEN_POWER_FAILURE,
            RefrigeratorMalfunction.REASON_FRIDGE_BREAKDOWN: config.Messages.FRIDGE_BROKEN_BREAKDOWN,
            RefrigeratorMalfunction.REASON_OTHER: config.Messages.FRIDGE_BROKEN_OTHER,
        }.get(reason)

    def respond_to_facility_user(self, reason):
        reason_desc = self.get_reason_desc(reason)
        self.respond(
            config.Messages.FRIDGE_BROKEN_RESPONSE,
            reason=self.msg.logistics_contact.translate(reason_desc)
        )

    def notify_district_users(self, supply_point, reason):
        recipients = Contact.objects.filter(
            is_active=True,
            supply_point__location=supply_point.location.parent,
            role__code__in=[config.Roles.DISTRICT_PHARMACIST, config.Roles.EPI_COORDINATOR]
        )

        reason_desc = self.get_reason_desc(reason)

        for recipient in recipients:
            recipient.message(
                config.Messages.FRIDGE_BROKEN_NOTIFICATION,
                reason=recipient.translate(reason_desc),
                facility=supply_point.code
            )

    def malfunction_exists(self, supply_point):
        malfunction = RefrigeratorMalfunction.get_open_malfunction(supply_point)

        if malfunction:
            days_since_report = (datetime.utcnow() - malfunction.reported_on).days
            self.respond(
                config.Messages.FRIDGE_MALFUNCTION_ALREADY_REPORTED,
                days=days_since_report
            )
            return True

        return False

    @logistics_contact_and_permission_required(config.Operations.REPORT_FRIDGE_MALFUNCTION)
    @require_facility
    def handle(self, text):
        supply_point = self.msg.logistics_contact.supply_point
        words = text.split()
        if self.is_text_valid(words):
            reason = words[0]
            if not self.malfunction_exists(supply_point):
                RefrigeratorMalfunction.new_malfunction(supply_point, reason, self.msg.logistics_contact)
                self.respond_to_facility_user(reason)
                self.notify_district_users(supply_point, reason)
