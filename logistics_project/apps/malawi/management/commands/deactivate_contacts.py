from datetime import datetime
from django.db import transaction
from django.core.management.base import BaseCommand
from rapidsms.models import Contact


class DeactivateContactCommand(BaseCommand):
    help = "Deactivates some contacts"
    log_file_name = None
    log_file = None

    def log(self, text):
        self.log_file.write("%s: %s\n" % (datetime.utcnow(), text))
        self.log_file.flush()

    def get_queryset(self):
        raise NotImplementedError()

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
        self.log('Deactivating %s contacts' % self.get_queryset().count())
        for contact in self.get_queryset():
            self.deactivate_contact(contact)

    def handle(self, *args, **options):
        with open(self.log_file_name, 'a') as log_file:
            self.log_file = log_file
            with transaction.commit_on_success():
                self.fix_contacts()
            self.log("%s active Contacts remain" % self.get_queryset().filter(is_active=True).count())
