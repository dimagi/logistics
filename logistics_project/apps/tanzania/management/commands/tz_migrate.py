from django.core.management.base import BaseCommand
from rapidsms.models import Connection, Contact, Backend
import csv
from logistics.models import ContactRole, SupplyPoint
from logistics_project.apps.tanzania.loader import init_static_data
from rapidsms.contrib.messagelog.models import Message
from django.utils.translation.trans_real import translation
from logistics_project.apps.migration import utils
from logistics_project.apps.tanzania.config import Messages
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes,\
    SupplyPointStatusValues, SupplyPointStatus
from dimagi.utils.django.management import are_you_sure
import os
import sys
from dimagi.utils.parsing import string_to_datetime
from logistics_project.apps.tanzania.migration import check_router,\
    unicode_csv_reader

def get_supply_point(name, code, type):
    """
    Get a supply point. Intentionally fail if not found.
    """
    if code:
        try:
            return SupplyPoint.objects.get(code__iexact=code.lower())
        except:
            print code
            raise
    else:
        try:
            return SupplyPoint.objects.get(name__iexact=name,
                                           type__name__iexact=type)
        except:
            print "%s: %s" % (type, name)
            raise
        
    
class Command(BaseCommand):
    help = "Migrate the tanzania data from the static messages file."

    def handle(self, *args, **options):
        init_static_data()
        
        def cleanup():
            Contact.objects.all().delete()
            Connection.objects.all().delete()
            Message.objects.all().delete()
    
        def load_contacts(file):
            print "loading contacts from %s" % file
            with open(file) as f:
                reader = csv.reader(f, delimiter=',', quotechar='"')
                idmap = {}
                for row in reader:
                    id, name, language, email, is_primary, role, _sp_id, \
                    sp_name, sp_code, sp_type, backend, phone = row
                    
                    # intentionally fail hard if this isn't present
                    role_obj = ContactRole.objects.get(name__iexact=role)
                    
                    sp = get_supply_point(sp_name, sp_code, sp_type)
                    if id not in idmap:
                        # todo commodities?
                        c = Contact.objects.create(name=name, language=language, 
                                                   is_active=is_primary, role=role_obj,
                                                   supply_point=sp, is_approved=True,
                                                   email=email)
                        idmap[id] = c
                    c = idmap[id]
                    if phone and backend=="push_backend":
                        # for real users, create a migration backend for them
                        # instead of the push backend, this will be cleaned later
                        # in the migration 
                        be = Backend.objects.get_or_create(name="migration")[0]
                        Connection.objects.get_or_create(backend=be, identity=phone,
                                                         contact=c)
                    elif phone and backend:
                        be = Backend.objects.get_or_create(name=backend)[0]
                        Connection.objects.create(backend=be, identity=phone,
                                                  contact=c)
                    
                        
            print "Migrated %s Contacts and %s Phone numbers" % \
                    (Contact.objects.count(), Connection.objects.count())
        
        def guess_status_from_outbound_message(text):
            def matches_in_any_language(string_to_translate, string_to_check):
                def clean(s):
                    return s.lower().strip()
                if clean(string_to_translate) == clean(string_to_check): return True
                for lang in ["en", "sw"]:
                    translated = translation(lang).gettext(string_to_translate)
                    if clean(translated) == clean(string_to_check):
                        return True
                    else:
                        pass
                        #print "%s is not %s" % (translated, string_to_check)
                
                return False
            
            if matches_in_any_language(Messages.REMINDER_STOCKONHAND, text):
                return (SupplyPointStatusTypes.SOH_FACILITY, SupplyPointStatusValues.REMINDER_SENT)
            if matches_in_any_language(Messages.REMINDER_R_AND_R_FACILITY, text):
                return (SupplyPointStatusTypes.R_AND_R_FACILITY, SupplyPointStatusValues.REMINDER_SENT)
            if matches_in_any_language(Messages.REMINDER_R_AND_R_DISTRICT, text):
                return (SupplyPointStatusTypes.R_AND_R_DISTRICT, SupplyPointStatusValues.REMINDER_SENT)
            if matches_in_any_language(Messages.REMINDER_DELIVERY_FACILITY, text):
                return (SupplyPointStatusTypes.DELIVERY_FACILITY, SupplyPointStatusValues.REMINDER_SENT)
            if matches_in_any_language(Messages.REMINDER_DELIVERY_DISTRICT, text):
                return (SupplyPointStatusTypes.DELIVERY_DISTRICT, SupplyPointStatusValues.REMINDER_SENT)
            if matches_in_any_language(Messages.REMINDER_SUPERVISION, text):
                return (SupplyPointStatusTypes.SUPERVISION_FACILITY, SupplyPointStatusValues.REMINDER_SENT)

            return (None, None)
        
        def load_messages(message_file):
            print "loading messages from %s" % message_file
            print "started"
            with open(message_file, 'r') as f:
                reader = unicode_csv_reader(f, delimiter=',', quotechar='"')
                inbound_count = outbound_count = 0
                inbound_max = outbound_max = 9999999999
                for row in reader:
                    pk1, pk2, pk3, dir, timestamp, text, phone = row
                    parsed_date = string_to_datetime(timestamp)
                    if dir == "I":
                        #print "%s: %s (%s)" % (phone, text, timestamp)
                        inbound_count = inbound_count + 1
                        try:
                            utils.send_test_message(identity=phone,
                                                    text=text,
                                                    timestamp=timestamp)
                        except Exception, e:
                            raise
                            
                        if inbound_count % 100 == 0:
                            print "processed %s inbound and %s outbound messages." % (inbound_count, outbound_count)
                    elif dir == "O":
                        status_type, status_value = guess_status_from_outbound_message(text)
                        if status_type and status_value:
                            outbound_count = outbound_count + 1
                        
                            # this is super janky, but we'll live with it
                            # hack it so that outbound reminders generate the
                            # appropriate supply point statuses in the db
                            notset = False
                            try:
                                connection = Connection.objects.get(identity=phone,
                                                                    backend__name="migration")
                                if connection.contact and connection.contact.supply_point:
                                    SupplyPointStatus.objects.create(status_type=status_type,
                                                                     status_value=status_value,
                                                                     status_date=parsed_date,
                                                                     supply_point=connection.contact.supply_point)
                                else:
                                    notset = True
                            except Connection.DoesNotExist:
                                notset = True
                            if notset:
                                print "No connection, contact, or supply point found for %s, so no status saved" % phone
                            
                    if inbound_count >= inbound_max:
                        break
                    if outbound_count >= outbound_max:
                        break
            print "processed %s incoming and %s outgoing messages" % (inbound_count, outbound_count)
            
        def clean_migration_backends():
            migration_connections = Connection.objects.filter(backend__name="migration")
            push_backend = Backend.objects.get_or_create(name="push_backend")[0]
            for conn in migration_connections:
                conn.backend = push_backend
                conn.save()
            print "moved %s migration connections to push backend" % migration_connections.count()
        
        def check_status():
            real_contacts = Contact.objects.filter(connection__backend__name="push_backend")
            failed = 0
            for contact in real_contacts:
                if contact.default_connection.backend.name != "push_backend":
                    print "contact %s has %s as default instead of push" % contact.default_connection
                    failed += 1
                if contact.connection_set.count() > 1:
                    print "found multiple connections"
            print "checked %s contacts" % real_contacts.count()
            if failed:
                print "Check FAILED for %s contacts. See output for more details"
            else:
                print "Check PASSED"
        
        print "checking router.."
        if not check_router():
            sys.exit()
        print "router running."
            
        if True or are_you_sure("really run the migration? (yes or no): "):
            cleanup()
            print "Starting migration!"
            datapath = os.path.join(os.path.dirname\
                                (os.path.dirname\
                                 (os.path.dirname\
                                  (os.path.dirname\
                                   (os.path.dirname\
                                    (os.path.abspath(os.path.dirname(__file__))))))),
                                "static", "tanzania", "migration")
            contact_file = os.path.join(datapath, "contacts.csv")
            load_contacts(contact_file)
            
            messages_file = os.path.join(datapath, "messages.csv")
            load_messages(messages_file)
            print "cleaning up"
            clean_migration_backends()
            print "checking status"
            check_status()
            
        else:
            print "Migration canceled."
        