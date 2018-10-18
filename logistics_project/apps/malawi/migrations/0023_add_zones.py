# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from static.malawi.config import SupplyPointCodes, LocationCodes


class Migration(DataMigration):

    location_content_type = None
    zone_supply_point_type = None
    zone_location_type = None
    country_location = None
    country_supply_point = None

    def get_or_create_zone_supply_point_type(self, orm):
        SupplyPointType = orm['logistics.SupplyPointType']

        obj, _ = SupplyPointType.objects.get_or_create(
            code=SupplyPointCodes.ZONE,
            defaults={'name': SupplyPointCodes.ALL[SupplyPointCodes.ZONE]},
        )
        obj.name = SupplyPointCodes.ALL[SupplyPointCodes.ZONE]
        obj.save()
        return obj

    def get_or_create_zone_location_type(self, orm):
        LocationType = orm['locations.LocationType']

        obj, _ = LocationType.objects.get_or_create(
            slug=LocationCodes.ZONE,
            defaults={'name': LocationCodes.ZONE},
        )
        obj.name = LocationCodes.ZONE
        obj.save()
        return obj

    def create_zone(self, orm, name, code, child_district_codes):
        SupplyPoint = orm['logistics.SupplyPoint']
        Location = orm['locations.Location']

        location, _ = Location.objects.get_or_create(code=code, defaults={'name': name})
        location.type = self.zone_location_type
        location.parent_type = self.location_content_type
        location.parent_id = self.country_location.pk
        location.name = name
        location.is_active = True
        location.save()

        supply_point, _ = SupplyPoint.objects.get_or_create(
            code=code,
            defaults={'name': name, 'type': self.zone_supply_point_type, 'location': location}
        )
        supply_point.name = name
        supply_point.active = True
        supply_point.type = self.zone_supply_point_type
        supply_point.location = location
        supply_point.supplied_by = self.country_supply_point
        supply_point.save()

        for code in child_district_codes:
            child_district = SupplyPoint.objects.get(code=code)
            if child_district.type_id != SupplyPointCodes.DISTRICT:
                raise RuntimeError("Expected District")

            child_district.supplied_by = supply_point
            child_district.save()

            child_location = child_district.location
            if child_location.type_id != LocationCodes.DISTRICT:
                raise RuntimeError("Expected District")

            child_location.parent_id = location.pk
            child_location.save()

    def forwards(self, orm):
        ContentType = orm['contenttypes.ContentType']
        SupplyPoint = orm['logistics.SupplyPoint']
        SupplyPointType = orm['logistics.SupplyPointType']
        Location = orm['locations.Location']
        LocationType = orm['locations.LocationType']

        try:
            self.location_content_type = ContentType.objects.get(app_label='locations', model='location')
            self.zone_supply_point_type = self.get_or_create_zone_supply_point_type(orm)
            self.zone_location_type = self.get_or_create_zone_location_type(orm)
            self.country_location = Location.objects.get(type__slug=LocationCodes.COUNTRY)
            self.country_supply_point = SupplyPoint.objects.get(type__code=SupplyPointCodes.COUNTRY)
        except ObjectDoesNotExist:
            # ignore on initial load / if nothing found
            return

        self.create_zone(orm, 'Northern', 'no', ['01', '02', '03', '04', '05', '06', '07'])
        self.create_zone(orm, 'Central Eastern', 'ce', ['10', '11', '12', '13', '14'])
        self.create_zone(orm, 'Central Western', 'cw', ['15', '16', '17', '18'])
        self.create_zone(orm, 'South Eastern', 'se', ['25', '26', '27', '32', '35', '36'])
        self.create_zone(orm, 'South Western', 'sw', ['28', '29', '30', '31', '33', '34', '37', '99'])

        if (
            SupplyPoint.objects
            .filter(type__code=SupplyPointCodes.DISTRICT, supplied_by=self.country_supply_point)
            .count()
        ) > 0:
            raise RuntimeError("Some district SupplyPoints do not have supplied_by set properly")

        if (
            Location.objects
            .filter(type__slug=LocationCodes.DISTRICT, parent_id=self.country_location.pk)
            .count()
        ) > 0:
            raise RuntimeError("Some district Locations do not have parent_id set properly")

        print "Successfully created zones and placed them into the Location/SupplyPoint hierarchy."

    def backwards(self, orm):
        pass

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.location': {
            'Meta': {'ordering': "['name']", 'object_name': 'Location'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locations'", 'null': 'True', 'to': "orm['locations.LocationType']"})
        },
        'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        'logistics.contactrole': {
            'Meta': {'object_name': 'ContactRole'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'responsibilities': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['logistics.Responsibility']", 'null': 'True', 'blank': 'True'})
        },
        'logistics.defaultmonthlyconsumption': {
            'Meta': {'unique_together': "(('supply_point_type', 'product'),)", 'object_name': 'DefaultMonthlyConsumption'},
            'default_monthly_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'supply_point_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPointType']"})
        },
        'logistics.historicalstockcache': {
            'Meta': {'object_name': 'HistoricalStockCache'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'month': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']", 'null': 'True'}),
            'stock': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'logistics.logisticsprofile': {
            'Meta': {'object_name': 'LogisticsProfile'},
            'can_view_facility_level_data': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_view_hsa_level_data': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'current_dashboard_base_level': ('django.db.models.fields.CharField', [], {'default': "'h'", 'max_length': '1'}),
            'designation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['malawi.Organization']", 'null': 'True', 'blank': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'logistics.nagrecord': {
            'Meta': {'object_name': 'NagRecord'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nag_type': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'report_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'warning': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'logistics.product': {
            'Meta': {'ordering': "['name']", 'object_name': 'Product'},
            'average_monthly_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'emergency_order_level': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'equivalents': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'equivalents_rel_+'", 'null': 'True', 'to': "orm['logistics.Product']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'product_code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sms_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10', 'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ProductType']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.productreport': {
            'Meta': {'object_name': 'ProductReport'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messagelog.Message']", 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'report_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow', 'db_index': 'True'}),
            'report_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ProductReportType']"}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"})
        },
        'logistics.productreporttype': {
            'Meta': {'object_name': 'ProductReportType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.productstock': {
            'Meta': {'unique_together': "(('supply_point', 'product'),)", 'object_name': 'ProductStock'},
            'auto_monthly_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'days_stocked_out': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'manual_monthly_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'use_auto_consumption': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'logistics.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'base_level': ('django.db.models.fields.CharField', [], {'default': "'h'", 'max_length': '1'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.requisitionreport': {
            'Meta': {'object_name': 'RequisitionReport'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messagelog.Message']"}),
            'report_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"})
        },
        'logistics.responsibility': {
            'Meta': {'object_name': 'Responsibility'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'logistics.stockrequest': {
            'Meta': {'object_name': 'StockRequest'},
            'amount_approved': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'amount_received': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'amount_requested': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'balance': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True'}),
            'canceled_for': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.StockRequest']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_emergency': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'received_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'received_by'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'received_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'requested_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requested_by'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'requested_on': ('django.db.models.fields.DateTimeField', [], {}),
            'responded_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responded_by'", 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'responded_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'response_status': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"})
        },
        'logistics.stocktransaction': {
            'Meta': {'object_name': 'StockTransaction'},
            'beginning_balance': ('django.db.models.fields.IntegerField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'ending_balance': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'product_report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ProductReport']", 'null': 'True'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"})
        },
        'logistics.stocktransfer': {
            'Meta': {'object_name': 'StockTransfer'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'closed_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'giver': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'giver'", 'null': 'True', 'to': "orm['logistics.SupplyPoint']"}),
            'giver_unknown': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initiated_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'receiver': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'receiver'", 'to': "orm['logistics.SupplyPoint']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'logistics.supplypoint': {
            'Meta': {'object_name': 'SupplyPoint'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['logistics.SupplyPointGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_reported': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'supplied_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPointType']"})
        },
        'logistics.supplypointgroup': {
            'Meta': {'object_name': 'SupplyPointGroup'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'logistics.supplypointtype': {
            'Meta': {'object_name': 'SupplyPointType'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True'}),
            'default_monthly_consumptions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['logistics.Product']", 'null': 'True', 'through': "orm['logistics.DefaultMonthlyConsumption']", 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.supplypointwarehouserecord': {
            'Meta': {'object_name': 'SupplyPointWarehouseRecord'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"})
        },
        'malawi.alert': {
            'Meta': {'object_name': 'Alert'},
            'eo_total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'eo_with_resupply': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'eo_without_resupply': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'have_stockouts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_hsas': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'order_readys': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'products_approved': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'products_requested': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'reporting_receipts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total_requests': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'without_products_managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'malawi.calculatedconsumption': {
            'Meta': {'object_name': 'CalculatedConsumption'},
            'calculated_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'time_needing_data': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'time_stocked_out': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'time_with_data': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.currentconsumption': {
            'Meta': {'object_name': 'CurrentConsumption'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'current_daily_consumption': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'stock_on_hand': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.historicalstock': {
            'Meta': {'object_name': 'HistoricalStock'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'stock': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.orderfulfillment': {
            'Meta': {'object_name': 'OrderFulfillment'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'quantity_received': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'quantity_requested': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.orderrequest': {
            'Meta': {'object_name': 'OrderRequest'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'emergency': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.organization': {
            'Meta': {'object_name': 'Organization'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managed_supply_points': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'malawi.productavailabilitydata': {
            'Meta': {'object_name': 'ProductAvailabilityData'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'emergency_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'good_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_emergency_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_good_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_over_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_under_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_with_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_without_data': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'managed_and_without_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'over_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'under_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {}),
            'with_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'without_data': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'without_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'malawi.productavailabilitydatasummary': {
            'Meta': {'object_name': 'ProductAvailabilityDataSummary'},
            'any_emergency_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_good_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_over_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_under_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_with_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_without_data': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_without_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'base_level': ('django.db.models.fields.CharField', [], {'default': "'h'", 'max_length': '1'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.refrigeratormalfunction': {
            'Meta': {'object_name': 'RefrigeratorMalfunction'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'malfunction_reason': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'reported_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['rapidsms.Contact']"}),
            'reported_on': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'resolved_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'responded_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'sent_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['logistics.SupplyPoint']"}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['logistics.SupplyPoint']"})
        },
        'malawi.reportingrate': {
            'Meta': {'object_name': 'ReportingRate'},
            'base_level': ('django.db.models.fields.CharField', [], {'default': "'h'", 'max_length': '1'}),
            'complete': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'on_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'reported': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.timetracker': {
            'Meta': {'object_name': 'TimeTracker'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'time_in_seconds': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'messagelog.message': {
            'Meta': {'object_name': 'Message'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']", 'null': 'True'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'direction': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.connection': {
            'Meta': {'unique_together': "(('backend', 'identity'),)", 'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'commodities': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'reported_by'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['logistics.Product']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'needs_reminders': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['malawi.Organization']", 'null': 'True', 'blank': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ContactRole']", 'null': 'True', 'blank': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['logistics', 'locations', 'contenttypes', 'malawi']
    symmetrical = True
