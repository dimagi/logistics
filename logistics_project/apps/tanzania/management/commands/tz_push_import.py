from logistics_project.apps.tanzania.migration import check_router,\
    unicode_csv_reader
from django.core.management.base import BaseCommand
from dimagi.utils.django.management import are_you_sure
from datetime import datetime
import os
import sys
from logistics_project.apps.migration import utils
from rapidsms.models import Backend, Connection

class Command(BaseCommand):
    help = "Import messages from a csv dump of Push gateway's inbound message log"

    def handle(self, *args, **options):
        def clear_migration_backends():
            migration_connections = Connection.objects.filter(backend__name="migration")
            if migration_connections.count():
                if are_you_sure(("Do you really want to delete %s migration connections? " 
                                 "This may have unintended consequences.") %migration_connections.count()):
                    migration_connections.all().delete()
                else:
                    print "You have to clear migration connections before starting."
                    sys.exit()
            
        def load_push_messages(message_file):
            print "loading messages from %s" % message_file
            print "started"
            migration_backend = Backend.objects.get_or_create(name="migration")[0]
            with open(message_file, 'r') as f:
                reader = unicode_csv_reader(f, delimiter=',', quotechar='"')
                inbound_count = -1
                max = 9999999999
                for row in reader:
                    inbound_count = inbound_count + 1
                    if inbound_count == 0:
                        continue # ignore the first line of headers
                    
                    msg, number, timestamp = row
                    
                    # if we already have a registered contact here
                    # then make sure we associate them with the migration
                    # backend before pumping the message through
                    try: 
                        push_conn = Connection.objects.get(backend__name="push_backend", 
                                                           identity=number)
                        push_conn.backend = migration_backend
                        push_conn.save()
                    except Connection.DoesNotExist:
                        # maybe they're newly created, no problem
                        pass
                        
                    parsed_date = datetime.strptime(timestamp, "%d/%m/%Y %H:%M:%S")
                    try:
                        utils.send_test_message(identity=number,
                                                text=msg,
                                                timestamp=str(parsed_date))
                    except Exception, e:
                        print e
                        raise
                        
                    if inbound_count % 100 == 0:
                        print "processed %s inbound messages." % (inbound_count)
                    if inbound_count >= max:
                        break
                    
            print "Complete. Processed %s incoming messages" % (inbound_count)

        def prompt_and_cleanup():
            are_you_sure("Enter any key to finalize cleanup. This should be done after the router has processed all messages")
            migration_connections = Connection.objects.filter(backend__name="migration")
            push_backend = Backend.objects.get_or_create(name="push_backend")[0]
            for conn in migration_connections:
                conn.backend = push_backend
                conn.save()
            print "moved %s migration connections to push backend" % migration_connections.count()
        
        
            
        print "checking router.."
        if not check_router():
            sys.exit()
        print "router running."
        
        if True or are_you_sure("really run the import? (yes or no): "):
            print "Starting migration!"
            datapath = os.path.join(os.path.dirname\
                                (os.path.dirname\
                                 (os.path.dirname\
                                  (os.path.dirname\
                                   (os.path.dirname\
                                    (os.path.abspath(os.path.dirname(__file__))))))),
                                "static", "tanzania", "push")
            
            message_file = os.path.join(datapath, "2011-09-09-PUSH-Messages.csv")
            clear_migration_backends()
            load_push_messages(message_file)
            prompt_and_cleanup()
        else:
            print "Migration canceled."
        