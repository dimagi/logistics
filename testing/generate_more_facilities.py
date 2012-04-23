#!/usr/bin/env python
from logistics.models import *
import random
from django.db.models.expressions import F
from django.db.models import Q, Sum, Max

NUM_NEW_FACILITIES = 5000
NUM_NEW_DISTRICTS = 500
NUM_NEW_REGIONS = 50
from csv import writer
w = writer(open("../static/tanzania/migration/all_facilities_perf_test.csv", "ab"))

#31,TANDAHIMBA,t,,MTWARA,REGION,,,,DISTRICT

start_id = SupplyPoint.objects.aggregate(id=Max('id'))['id']

REGION_START_ID = start_id
DISTRICT_START_ID = REGION_START_ID + NUM_NEW_REGIONS
FACILITY_START_ID = DISTRICT_START_ID + NUM_NEW_DISTRICTS

# id, name, is_active, msd_code, parent_name, parent_type, lat, lon, group, type

for dist_id in range(REGION_START_ID, DISTRICT_START_ID):
    w.writerow([dist_id,"Test Region %s" % dist_id, 't', '', 'MOHSW', "MOHSW",'','','',"REGION" ])

for dist_id in range(DISTRICT_START_ID, FACILITY_START_ID):
    parent_region = "Test Region %s" % random.randint(REGION_START_ID, DISTRICT_START_ID-1)
    w.writerow([dist_id,"Test District %s" % dist_id, 't', '', parent_region, "REGION",'','','',"DISTRICT" ])

for fac_id in range(FACILITY_START_ID, FACILITY_START_ID + NUM_NEW_FACILITIES):
    parent_district = "Test District %s" % random.randint(DISTRICT_START_ID, FACILITY_START_ID-1)
    w.writerow([fac_id, "Test Facility %s" % fac_id, 't', "D9%04d" % fac_id, parent_district,'DISTRICT','','',random.choice('ABC'),'FACILITY'])
