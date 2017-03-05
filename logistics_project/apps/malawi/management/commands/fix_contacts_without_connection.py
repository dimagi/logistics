from datetime import datetime
from django.db import transaction
from django.core.management.base import BaseCommand
from rapidsms.models import Contact, Connection
from static.malawi.config import SupplyPointCodes


class Command(BaseCommand):
    help = "Deactivates contacts that don't have a connection"
    log_file = None

    def log(self, text):
        self.log_file.write("%s: %s\n" % (datetime.utcnow(), text))
        self.log_file.flush()

    def get_queryset(self):
        return Contact.objects.filter(connection__id__isnull=True)

    def deactivate_contact(self, contact):
        """
        Perform the same actions as if the contact had texted in "leave"
        """
        self.log("--- Processing contact %s ---" % contact.pk)
        if contact.is_active:
            self.log("Contact is active, deactivating...")
            contact.is_active = False
            contact.save()
        else:
            self.log("Contact is already deactivated, ignoring...")

        if contact.supply_point:
            self.log("Contact's supply point type is: %s" % contact.supply_point.type_id)
            if contact.supply_point.type_id == SupplyPointCodes.HSA:
                supply_point = contact.supply_point
                location = supply_point.location
                self.log(
                    "HSA detected, checking supply point %s and location %s" %
                    (supply_point.pk, location.pk)
                )
                if supply_point.active:
                    if supply_point.active_contact_set.count() == 0:
                        self.log("SupplyPoint is active with no active contacts, deactivating...")
                        supply_point.active = False
                        supply_point.save()
                        location.is_active = False
                        location.save()
                    else:
                        self.log("SupplyPoint is active with but has other active contacts, ignoring...")
                else:
                    self.log("SupplyPoint is already deactivated")

    def fix_contacts(self):
        for contact in self.get_queryset():
            self.deactivate_contact(contact)

    def handle(self, *args, **options):
        with open('contact-deactivate-fix.txt', 'a') as log_file:
            self.log_file = log_file
            with transaction.commit_on_success():
                self.fix_contacts()
            self.log("%s Contacts remain without a connection" % self.get_queryset().count())
