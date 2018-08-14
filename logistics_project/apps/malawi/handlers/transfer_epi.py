from datetime import datetime
from logistics.decorators import logistics_contact_and_permission_required
from logistics.models import ContactRole, SupplyPoint
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics_project.apps.malawi.util import get_supervisors, swallow_errors
from logistics_project.decorators import require_district
from logistics.util import config
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact


class AdviseEPITransferHandler(KeywordHandler):
    keyword = "transfer"

    def help(self):
        self.handle("")

    def is_text_valid(self, words):
        if len(words) != 2:
            self.respond(config.Messages.FACILITY_TRANSFER_HELP)
            return False

        return True

    def get_facility(self, code, district_supply_point, perform_location_parent_check=True):
        try:
            facility = SupplyPoint.objects.get(code=code, type__code=config.SupplyPointCodes.FACILITY)
        except SupplyPoint.DoesNotExist:
            facility = None

        if (
            facility is None or
            not facility.active or
            (perform_location_parent_check and facility.location.parent != district_supply_point.location)
        ):
            self.respond(config.Messages.FACILITY_NOT_FOUND, facility=code)
            return None

        return facility

    def respond_to_district_users(self, from_facility):
        recipients = get_supervisors(self.msg.logistics_contact.supply_point)
        for recipient in recipients:
            with swallow_errors():
                recipient.message(config.Messages.TRANSFER_RESPONSE_TO_DISTRICT, facility=from_facility.code)

    def notify_facility_users(self, malfunction, to_facility):
        malfunction.reported_by.message(config.Messages.TRANSFER_MESSAGE_TO_FACILITY, facility=to_facility.code)

    @logistics_contact_and_permission_required(config.Operations.ADVISE_FACILITY_TRANSFER)
    @require_district
    def handle(self, text):
        words = text.split()
        if self.is_text_valid(words):
            district_supply_point = self.msg.logistics_contact.supply_point
            from_facility = self.get_facility(words[0], district_supply_point)
            if from_facility is None:
                return

            to_facility = self.get_facility(words[1], district_supply_point, perform_location_parent_check=False)
            if to_facility is None:
                return

            if from_facility == to_facility:
                self.respond(config.Messages.FACILITY_MUST_BE_DIFFERENT)
                return

            malfunction = RefrigeratorMalfunction.get_open_malfunction(from_facility)
            if not malfunction:
                self.respond(config.Messages.FRIDGE_NOT_REPORTED_BROKEN_FOR_FACILITY, facility=from_facility.code)
                return

            if RefrigeratorMalfunction.get_open_malfunction(to_facility):
                self.respond(config.Messages.FRIDGE_REPORTED_BROKEN_FOR_FACILITY, facility=to_facility.code)
                return

            malfunction.sent_to = to_facility
            malfunction.responded_on = datetime.utcnow()
            malfunction.save()

            self.notify_facility_users(malfunction, to_facility)
            self.respond_to_district_users(from_facility)
