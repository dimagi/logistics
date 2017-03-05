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
        The supply point and location are deactivated in logistics_project.apps.malawi.signals.deactivate_hsa_location
        """
        self.log("--- Processing contact %s ---" % contact.pk)
        if contact.is_active:
            self.log("Contact is active, deactivating...")
            contact.is_active = False
            contact.save()
        else:
            self.log("Contact is already deactivated, ignoring...")

    def fix_contacts(self):
        for contact in self.get_queryset():
            self.deactivate_contact(contact)

    def handle(self, *args, **options):
        with open('contact-deactivate-fix.txt', 'a') as log_file:
            self.log_file = log_file
            with transaction.commit_on_success():
                self.fix_contacts()
            self.log("%s active Contacts remain without a connection" % self.get_queryset().filter(is_active=True).count())
