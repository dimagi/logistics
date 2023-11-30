from rapidsms.models import Contact, Connection, Backend
from logistics.models import ContactRole, SupplyPoint, Product, SupplyPointType, ProductReportsHelper, StockRequest
from rapidsms.contrib.locations.models import Location, Point, LocationType
from logistics.util import config
from logistics.shortcuts import create_stock_report
from geopy.geocoders import Nominatim
from phone_gen import PhoneNumber
import os
import pandas as pd
from datetime import datetime
import random
# read data from csv files
DATA_DIR = os.path.join(os.getcwd(), "data")
name_data_fpath = os.path.join(DATA_DIR, "malawian_names.csv")
district_data_fpath = os.path.join(DATA_DIR, "districts_points.csv")
facility_data_fpath = os.path.join(DATA_DIR, "facilities_points.csv")

names_data = pd.read_csv(name_data_fpath)
fnames = list(names_data["fname"].values)
lnames = list(names_data["lname"].values)

district_data = pd.read_csv(district_data_fpath, dtype={'code':str})
district_codes = list(district_data["code"].values)
district_latitudes = list(district_data["latitude"].values)
district_longitudes = list(district_data["longitude"].values)

facility_data = pd.read_csv(facility_data_fpath)
facility_ids = list(facility_data["facility_id"].values)
fac_latitudes = list(facility_data["latitude"].values)
fac_longitudes = list(facility_data["longitude"].values)

# 1. Populate initial coordinates (all districts, 26 facilities across 5 districts)
# a) Populate coordinates for all districts
for (code, lat, long) in zip(district_codes, district_latitudes, district_longitudes):
    supply_point = SupplyPoint.objects.get(code=code)
    location = supply_point.location
    point = Point(latitude=lat, longitude=long)
    point.save()
    location.point = point
    location.save()

# b) Populate coordinates for health facilities
for (id, lat, long) in zip(facility_ids, fac_latitudes, fac_longitudes):
    supply_point = SupplyPoint.objects.get(pk=id)
    location = supply_point.location
    point = Point(latitude=lat, longitude=long)
    point.save()
    location.point = point
    location.save()

# 2. Register contacts and supply points for the health facilities
# a) retrieve supply points and respective codes
locations = Location.objects.filter(point__isnull=False, type_id='facility')
location_codes = [loc.code for loc in locations]
supply_points = SupplyPoint.objects.filter(code__in=location_codes)

# b) iterate locations and create new locations, supply points, contacts, associate products, and record product stock
hsa_loc_type = LocationType.objects.get(slug='hsa')
hsa_sup_point_type = SupplyPointType.objects.get(code='hsa')
hsa_contact_role = ContactRole.objects.get(code='hsa')
backend = Backend.objects.get(pk=1)
phone_number_gen = PhoneNumber("MW")

for supply_point in supply_points:
    for i in range(1, 5):
        # generate id and name
        hsa_id = "%s%02d" % (supply_point.code, i)
        contact_name = "%s %s" % (random.choice(fnames), random.choice(lnames))
        print(f"Processing {contact_name} {hsa_id}")
        # create location
        hsa_loc = Location.objects.create(name=contact_name, type=hsa_loc_type, code=hsa_id, parent=supply_point.location)
        # create supply point
        sp = SupplyPoint.objects.create(name=contact_name, code=hsa_id, type=config.hsa_supply_point_type(),location=hsa_loc, supplied_by=supply_point)

        # create contact
        contact = Contact(name=contact_name, supply_point=sp, role=hsa_contact_role,is_active=True,is_approved=True)
        contact.save()

        # create connection
        phone_number = phone_number_gen.mobile_number()
        connection = Connection(backend=backend, identity=phone_number, contact=contact)
        connection.save()

        # associate with products
        available_products = [p for p in Product.objects.filter(type__base_level='h', is_active=True)]
        selected_products = random.sample(available_products, k=5)

        soh_report = []
        rec_report = []

        for product in selected_products:
            sp.activate_product(product)
            contact.commodities.add(product)
            contact.save()

            soh_quantity = random.randint(1, product.average_monthly_consumption)
            rec_quantity = random.randint(1, product.average_monthly_consumption) + 5
            soh_report.append(f"{product.sms_code} {soh_quantity}")
            rec_report.append(f"{product.sms_code} {rec_quantity}")

        # add stock records
        # report stock on hand using SOH message pattern
        soh_text = " ".join(soh_report)
        soh_stock_report = create_stock_report("soh",sp,soh_text)
        stock_requests = StockRequest.create_from_report(soh_stock_report,contact)

        # confirm readiness of order
        #pending_reqs = StockRequest.pending_requests().filter(supply_point=supply_point)
        for req in stock_requests:
            req.approve(contact, datetime.utcnow(), req.amount_requested)

        # confirm receipt of products
        rec_text = " ".join(soh_report)
        rec_stock_report = ProductReportsHelper(sp,'rec')
        rec_stock_report.newparse(rec_text)
        rec_stock_report.save()
        StockRequest.close_pending_from_receipt_report(rec_stock_report, contact)
