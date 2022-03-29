from __future__ import unicode_literals
from datetime import datetime
from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand


class DeactivateContactCommand(BaseCommand):
    help = "Deactivates some contacts"
    log_file_name = None
    log_file = None
    option_list = BaseCommand.option_list + (
        make_option('--limit', action='store', dest='limit', default=None,
                    help='Number of contacts to operate on.'),
        make_option('--test', action='store_true', dest='test', default=False,
                    help='Work in test mode (does not write to the database).'),
    )
    args = '[--limit <limit> --test]'
    limit = None
    test = False


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
        self.log("--- Processing contact %s %s ---" % (contact.pk, contact))
        if contact.is_active:
            self.log("Contact is active, deactivating...")
            contact.is_active = False
            if not self.test:
                contact.save()
        else:
            self.log("Contact is already deactivated, ignoring...")

    def fix_contacts(self):
        self.log('Deactivating %s contacts' % self.get_queryset().count())
        queryset = self.get_queryset()
        if self.limit:
            queryset = queryset[:self.limit]
        for contact in queryset:
            self.deactivate_contact(contact)

    def handle(self, *args, **options):
        limit = options.get('limit', None)
        if limit is not None:
            limit = int(limit)
        self.limit = limit
        self.test = options.get('test')
        with open(self.log_file_name, 'a') as log_file:
            self.log_file = log_file
            with transaction.atomic():
                self.fix_contacts()
            self.log("%s active Contacts remain" % self.get_queryset().filter(is_active=True).count())
