from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.core.management.base import BaseCommand
from rapidsms.models import Connection, Backend
from static.malawi.config import TNM_BACKEND_NAME, AIRTEL_BACKEND_NAME, TEST_BACKEND_NAME


class Command(BaseCommand):
    help = "Fixes duplicate Connnections"
    log_file = None

    tnm_backend = None
    airtel_backend = None
    test_backend = None

    def load_backends(self):
        self.tnm_backend = Backend.objects.get(name=TNM_BACKEND_NAME)
        self.airtel_backend = Backend.objects.get(name=AIRTEL_BACKEND_NAME)
        self.test_backend = Backend.objects.get(name=TEST_BACKEND_NAME)

    def log(self, text):
        self.log_file.write("%s: %s\n" % (datetime.utcnow(), text))
        self.log_file.flush()

    def get_queryset(self):
        return Connection.objects.filter(
            Q(identity__startswith='+265') | Q(identity__startswith='265'),
            backend=self.test_backend,
        )

    def unassign_connection(self, connection):
        self.log("Unassigning connection %s, %s, %s" % (connection.id, connection.contact_id, connection.identity))
        connection.contact_id = None
        connection.save()

    def contact_has_real_connections(self, contact):
        return Connection.objects.filter(
            contact=contact,
            backend__in=[self.tnm_backend, self.airtel_backend],
        ).count() > 0

    def deactivate_contact(self, contact):
        """
        Perform the same actions as if the contact had texted in "leave"
        The supply point and location are deactivated in logistics_project.apps.malawi.signals.deactivate_hsa_location
        """
        self.log("Deactivating contact %s" % contact.id)
        contact.is_active = False
        contact.save()

    def fix_connections(self):
        for connection in self.get_queryset():
            self.log("--- Processing connection %s ---" % connection.id)

            if connection.backend_id != self.test_backend.id:
                # As a precaution
                raise RuntimeError("Connection is not tied to test backend - check query")

            if connection.contact_id is None:
                self.log("Connection does not belong to a contact, nothing to do")
            else:
                self.log("Connection belongs to contact %s" % connection.contact_id)

                if not connection.contact.is_active:
                    self.log("Test connection belongs to inactive contact")
                    self.unassign_connection(connection)
                else:
                    if self.contact_has_real_connections(connection.contact):
                        self.log("Contact has either Airtel or TNM Connection")
                        self.unassign_connection(connection)
                    elif connection.contact.id in (6059, 6060, 6234):
                        self.log("Found one of (6059, 6060, 6234)")
                        # These contacts all only have one Connection, and it is tied to the test backend,
                        # and they also have all reregistered as new, currently active contacts, so we
                        # can just deactivate these old contacts.
                        self.deactivate_contact(connection.contact)
                        self.unassign_connection(connection)
                    else:
                        # There should be none of these, but will handle these manually in case there are
                        self.log("Skipping %s, please handle manually" % connection.contact_id)

    def handle(self, *args, **options):
        self.load_backends()
        with open('fix-message-tester-connections.txt', 'a') as log_file:
            self.log_file = log_file
            with transaction.atomic():
                self.fix_connections()
