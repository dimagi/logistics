from django.core.management.base import BaseCommand
from dimagi.utils.django.management import are_you_sure
from rapidsms.models import Connection, Contact, Backend
import os
import csv
from logistics.models import ContactRole, SupplyPoint
from logistics_project.apps.tanzania.loader import init_static_data
from couchdb.client import Row
from dimagi.utils.parsing import string_to_datetime
from rapidsms.router import router
from django.core.management import call_command
from rapidsms.contrib.ajax.exceptions import RouterNotResponding, RouterError
import sys
from rapidsms.contrib.messagelog.models import Message
from logistics_project.apps.migration import utils

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
                                                   supply_point=sp, is_approved=True)
                        idmap[id] = c
                    c = idmap[id]
                    if backend and phone:
                        be = Backend.objects.get_or_create(name=backend)[0]
                        Connection.objects.create(backend=be, identity=phone,
                                                  contact=c)
                    if phone and backend=="push_backend":
                        # for real users, also create a migration backend for them 
                        be = Backend.objects.get_or_create(name="migration")[0]
                        Connection.objects.get_or_create(backend=be, identity=phone,
                                                         contact=c)
                        
            print "Migrated %s Contacts and %s Phone numbers" % \
                    (Contact.objects.count(), Connection.objects.count())
        
        def load_messages(message_file):
            print "loading messages from %s" % message_file
            print "started"
            with open(message_file) as f:
                reader = csv.reader(f, delimiter=',', quotechar='"')
                count = 0
                max = 9999999999
                for row in reader:
                    pk1, pk2, pk3, dir, timestamp, text, phone = row
                    if dir == "I":
                        #print "%s: %s (%s)" % (phone, text, timestamp)
                        count = count + 1
                        try:
                            utils.send_test_message(identity=phone,
                                                    text=text,
                                                    timestamp=timestamp)
                        except RouterError, e:
                            print e.code
                            print e.content_type
                            print e.response
                            raise
                            
                        if count % 100 == 0:
                            print "processed %s messages." % count
                    
                    if count >= max:
                        break
            print "processed %s incoming messages" % count
            pass
        
        def check_router():
            # quasi-stolen from the httptester
            try:
                utils.check_status()
                return True
            except RouterNotResponding:
                print "The router is not available! Remember to start the rapidsms " \
                  "router before running the migration. FAIL."
            except RouterError:
                print "The router appears to be running but returned an error. " \
                      "Is the migration app in your installed_apps list? and " \
                      "have you enabled the migration backend?" 
                return False
                
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
            
        else:
            print "Migration canceled."
        