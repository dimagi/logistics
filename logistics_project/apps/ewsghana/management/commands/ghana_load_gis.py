import sys
import csv
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Load GIS data for ghana"

    def handle(self, *args, **options):
        if len(args) != 1:
            print "Please specify the csv file from where to load facilities"
            return
        self.add_GIS(args[0])
        
    def add_GIS(self, filename):
        from logistics.models import SupplyPoint, SupplyPointType
        from logistics.models import Location
        from rapidsms.contrib.locations.models import Point

        reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
        no_match = []
        match = []
        points_created = 0
        for row in reader:
            facility_name = row[3].strip().lower()
            first_part_of_facility_name = facility_name.split()[0]
            sp = None
            if first_part_of_facility_name == 'st' or first_part_of_facility_name == 'st.':
                second_part_of_facility_name = facility_name.split()[1]
                #print 'Trying to match %s' % facility_name
                try: 
                    sp = SupplyPoint.objects.get(name__icontains=second_part_of_facility_name)
                except:
                    no_match.append(facility_name)
                else:
                    print "   %s \t\t\t %s" % (facility_name, sp.name)
                    match.append(sp)
            else:
                #print 'Trying to match %s' % facility_name
                try: 
                    sp = SupplyPoint.objects.get(name__istartswith="%s " % first_part_of_facility_name)
                except:
                    no_match.append(facility_name)
                else:
                    print "   %s \t\t\t %s" % (facility_name, sp.name)
                    match.append(sp)
            if sp is not None and sp.location is not None and sp.location.point is None:
                location = sp.location
                latitude = row[4].strip()
                longitude = row[5].strip()
                p = Point.objects.create(latitude=latitude, longitude=longitude)
                location.point = p
                location.save()
                points_created = points_created + 1
        print "Matched Locations: %s" % len(match)
        print "Unmatched Locations: %s" % len(no_match)
        print "Points created: %s" % points_created
