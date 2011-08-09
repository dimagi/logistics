from django.core.management.base import BaseCommand
from dimagi.utils.django.management import are_you_sure
from rapidsms.models import Connection, Contact, Backend
import os
import csv
from logistics.apps.logistics.models import ContactRole, SupplyPoint
from logistics_project.apps.tanzania.loader import init_static_data

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
        
        def cleanup(self):
            Contact.objects.all().delete()
            Connection.objects.all().delete()
        
    
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
                        
            print "Migrated %s Contacts and %s Phone numbers" % \
                    (Contact.objects.count(), Connection.objects.count())
        
        if True or are_you_sure("really run the migration? (yes or no): "):
            print "Starting migration!"
            file = os.path.join(os.path.dirname\
                                (os.path.dirname\
                                 (os.path.dirname\
                                  (os.path.dirname\
                                   (os.path.dirname\
                                    (os.path.abspath(os.path.dirname(__file__))))))),
                                "static", "tanzania", "migration", "contacts.csv")
            load_contacts(file)
            
        else:
            print "Migration canceled."
        