from logistics.models import SupplyPoint
from csv import writer
import random
from django.core.management.base import LabelCommand, CommandError
from django.db.models.aggregates import Max
import os
import tempfile
from logistics_project.apps.tanzania.loader import load_locations


class Command(LabelCommand):
    help = "Generate dummy facilities."
    args = "<num_facilities>, <output_location>"
    label = "number of facilities to generate, number of facilities per district"
    
    def handle(self, *args, **options):
        if len(args) < 1: raise CommandError('Please specify %s.' % self.label.split(",")[0])
            
        num_facs = int(args[0])
        facs_per_dist = int(args[1]) if len(args) > 1 else 10
        num_dists = num_facs / facs_per_dist or 1 # make at least 1
        num_regs = num_facs / (facs_per_dist * facs_per_dist) or 1 # make at least 1

        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            w = writer(f)
            #31,TANDAHIMBA,t,,MTWARA,REGION,,,,DISTRICT
            start_id = SupplyPoint.objects.aggregate(id=Max('id'))['id']
            
            REGION_START_ID = start_id
            DISTRICT_START_ID = REGION_START_ID + num_regs
            FACILITY_START_ID = DISTRICT_START_ID + num_dists
            
            # id, name, is_active, msd_code, parent_name, parent_type, lat, lon, group, type
            
            for dist_id in range(REGION_START_ID, DISTRICT_START_ID):
                w.writerow([dist_id,"Test Region %s" % dist_id, 't', '', 'MOHSW', "MOHSW",'','','',"REGION" ])
            
            for dist_id in range(DISTRICT_START_ID, FACILITY_START_ID):
                parent_region = "Test Region %s" % random.randint(REGION_START_ID, DISTRICT_START_ID-1)
                w.writerow([dist_id,"Test District %s" % dist_id, 't', '', parent_region, "REGION",'','','',"DISTRICT" ])
            
            for fac_id in range(FACILITY_START_ID, FACILITY_START_ID + num_facs):
                parent_district = "Test District %s" % random.randint(DISTRICT_START_ID, FACILITY_START_ID-1)
                w.writerow([fac_id, "Test Facility %s" % fac_id, 't', "D9%04d" % fac_id, parent_district,'DISTRICT','','',random.choice('ABC'),'FACILITY'])
        
        load_locations(path)
        print "wrote %s new regions, %s new districts, %s new facilities" % \
            (num_regs, num_dists, num_facs)