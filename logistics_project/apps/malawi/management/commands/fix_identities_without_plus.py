import re
from datetime import datetime
from django.db import transaction
from django.core.management.base import BaseCommand
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Connection

TNM_BACKEND = 'tnm-smpp'


class Command(BaseCommand):
    help = "Fixes TNM identities without plus"
    log_file = None

    def log(self, text):
        self.log_file.write("%s: %s\n" % (datetime.utcnow(), text))
        self.log_file.flush()

    def cleanup_old_migration(self):
        """
        Perform cleanup from https://github.com/dimagi/logistics/pull/161
        """

        # Deprecated identities should not be tied to contacts
        self.log("Cleaning up deprecated connections...")
        for connection in Connection.objects.filter(identity__endswith='-deprecated'):
            self.unassign_connection(connection)

    def create_connection_with_plus(self, connection_without_plus):
        self.log("Unassigning connection and creating connection with plus for it")

        # Disassociate the old connection from the contact, but don't delete the connection. This
        # preserves the history in the message log.
        contact_id = connection_without_plus.contact_id
        connection_without_plus.contact_id = None
        connection_without_plus.save()

        # Create the new connection from the old one, associating it to the contact
        connection_with_plus = connection_without_plus
        connection_with_plus.pk = None
        connection_with_plus.identity = self.get_identity_with_plus(connection_without_plus)
        connection_with_plus.contact_id = contact_id
        connection_with_plus.save()

        self.log("Created connection with plus %s, %s, %s" %
            (connection_with_plus.pk, connection_with_plus.contact_id, connection_with_plus.identity)
        )

    def reassign_connection(self, from_connection, to_connection):
        to_connection.contact_id = from_connection.contact_id
        to_connection.save()
        self.log("Assigned to connection %s, %s, %s" % (to_connection.pk, to_connection.contact_id, to_connection.identity))

        from_connection.contact_id = None
        from_connection.save()
        self.log("Unassigned from connection %s, %s, %s" % (from_connection.pk, from_connection.contact_id, from_connection.identity))

    def unassign_connection(self, connection):
        if connection.contact_id is not None:
            self.log("Unassigning connection %s, %s, %s" % (connection.pk, connection.contact_id, connection.identity))
            connection.contact_id = None
            connection.save()

    def get_identity_with_plus(self, connection_without_plus):
        return '+%s' % connection_without_plus.identity

    def get_connection_with_plus(self, connection_without_plus):
        try:
            return Connection.objects.get(
                backend__name=TNM_BACKEND,
                identity=self.get_identity_with_plus(connection_without_plus),
            )
        except Connection.DoesNotExist:
            return None

    def get_queryset(self):
        # I confirmed there are no connections with duplicate identities within the TNM backend, so this will
        # be a distinct list of phone numbers.
        return Connection.objects.filter(
            backend__name=TNM_BACKEND,
            identity__startswith='265',
            contact__id__isnull=False, # It won't let me just filter on contact_id__isnull
        )

    def get_last_registration_timestamp(self, connection):
        return Message.objects.filter(
            connection=connection,
            direction='O',
            text__icontains='you have been registered for the cStock System'
        ).order_by('-date').values_list('date', flat=True)[0]

    def fix_phone_numbers(self):
        self.log("Beginning TNM phone number fix. See http://manage.dimagi.com/default.asp?247021 for details.")
        self.cleanup_old_migration()

        num_skipped = 0

        for connection_without_plus in list(self.get_queryset()):
            self.log("--- Processing connection %s, %s, %s ---" % (connection_without_plus.pk, connection_without_plus.contact_id, connection_without_plus.identity))

            # Based on our filter conditions, we know about connection_without_plus that:
            # - its identity does not start with a plus but starts with the country code
            # - it's tied to a contact; we can ignore connections that are not tied to a contact

            if re.match("^265\d{9}$", connection_without_plus.identity) is None:
                # I didn't see any data like this besides the deprecated ones, but log here in case
                self.log("Skipping due to invalid number format")
                num_skipped += 1
                continue

            connection_with_plus = self.get_connection_with_plus(connection_without_plus)
            if connection_with_plus:
                self.log("Connection found with plus %s, %s, %s" % (connection_with_plus.pk, connection_with_plus.contact_id, connection_with_plus.identity))

            if connection_with_plus is None:
                # The easiest of cases. A connection only exists without the plus and not with it.
                self.log('Connection does not exist with plus, will create one')
                self.create_connection_with_plus(connection_without_plus)

            elif connection_with_plus.contact_id is None:
                # The next easiest case. A connection exists with the plus but is not tied to a contact.
                self.reassign_connection(connection_without_plus, connection_with_plus)

            else:
                # The toughest case. Connections exist with the plus and without it, and both are tied to a contact.
                # Inactive contacts can't do any reporting, and also don't get notifications (e.g. the facility user
                # in the HSA workflow). So the approach is to assign the number with the plus to the active contact.

                if connection_with_plus.contact.is_active and connection_without_plus.contact.is_active:
                    self.log("Both contacts active")

                    if connection_with_plus.contact_id == connection_without_plus.contact_id:
                        # If it's the same contact, just unassign the connection without the plus.
                        self.log("Contacts are the same")
                        self.unassign_connection(connection_without_plus)

                    else:
                        # If the contacts are different, look up who registered last and make the
                        # connection with the plus be tied to them, while blanking out the contact association
                        # for the connection that has no plus.
                        contact1 = connection_without_plus.contact
                        contact2 = connection_with_plus.contact
                        timestamp1 = self.get_last_registration_timestamp(connection_without_plus)
                        timestamp2 = self.get_last_registration_timestamp(connection_with_plus)
                        self.log("%s last registered %s" % (contact1.id, timestamp1))
                        self.log("%s last registered %s" % (contact2.id, timestamp2))

                        if timestamp2 > timestamp1:
                            self.log("Connection with plus has registered later, keeping it")
                            self.unassign_connection(connection_without_plus)
                        else:
                            self.log("Connection without plus has registered later, reassigning contact")
                            self.reassign_connection(connection_without_plus, connection_with_plus)

                elif connection_without_plus.contact.is_active:
                    self.log("Only contact without plus is active")
                    self.reassign_connection(connection_without_plus, connection_with_plus)

                elif connection_with_plus.contact.is_active:
                    self.log("Only contact with plus is active")
                    self.unassign_connection(connection_without_plus)

                else:
                    self.log("Neither contact is active")
                    self.unassign_connection(connection_without_plus)

        self.log("%s numbers were skipped" % num_skipped)

    def handle(self, *args, **options):
        with open('tnm-phone-number-fix.txt', 'a') as log_file:
            self.log_file = log_file
            with transaction.commit_on_success():
                self.fix_phone_numbers()
            self.log("%s TNM Connections remain without a plus that are tied to a contact" % self.get_queryset().count())
