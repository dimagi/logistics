# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TimeTracker'
        db.create_table('malawi_timetracker', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('supply_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('total', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('time_in_seconds', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
        ))
        db.send_create_signal('malawi', ['TimeTracker'])

        # Adding model 'OrderFulfillment'
        db.create_table('malawi_orderfulfillment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('supply_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.Product'])),
            ('total', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('quantity_requested', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('quantity_received', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('malawi', ['OrderFulfillment'])

        # Adding model 'Alert'
        db.create_table('malawi_alert', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('supply_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'])),
            ('num_hsas', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('have_stockouts', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('eo_with_resupply', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('eo_without_resupply', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_requests', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('reporting_receipts', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('without_products_managed', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('malawi', ['Alert'])

        # Adding model 'ReportingRate'
        db.create_table('malawi_reportingrate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('supply_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('total', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('reported', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('on_time', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('complete', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('malawi', ['ReportingRate'])

        # Adding model 'UserProfileData'
        db.create_table('malawi_userprofiledata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('supply_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'])),
            ('facility_children', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('hsa_children', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('hsa_supervisors', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('contacts', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('supervisor_contacts', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('in_charge', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('contact_info', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('products_managed', self.gf('django.db.models.fields.TextField')()),
            ('last_message', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['messagelog.Message'], null=True)),
        ))
        db.send_create_signal('malawi', ['UserProfileData'])

        # Adding model 'OrderRequest'
        db.create_table('malawi_orderrequest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('supply_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.Product'])),
            ('total', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('emergency', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('malawi', ['OrderRequest'])

        # Adding model 'ProductAvailabilityDataSummary'
        db.create_table('malawi_productavailabilitydatasummary', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('supply_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('total', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('any_managed', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('any_without_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('any_with_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('any_under_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('any_over_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('any_good_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('any_without_data', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('malawi', ['ProductAvailabilityDataSummary'])

        # Adding model 'ProductAvailabilityData'
        db.create_table('malawi_productavailabilitydata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('supply_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.Product'])),
            ('total', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('managed', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('with_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('under_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('good_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('over_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('without_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('without_data', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('managed_and_with_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('managed_and_under_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('managed_and_good_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('managed_and_over_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('managed_and_without_stock', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('managed_and_without_data', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('malawi', ['ProductAvailabilityData'])

    def backwards(self, orm):
        # Deleting model 'TimeTracker'
        db.delete_table('malawi_timetracker')

        # Deleting model 'OrderFulfillment'
        db.delete_table('malawi_orderfulfillment')

        # Deleting model 'Alert'
        db.delete_table('malawi_alert')

        # Deleting model 'ReportingRate'
        db.delete_table('malawi_reportingrate')

        # Deleting model 'UserProfileData'
        db.delete_table('malawi_userprofiledata')

        # Deleting model 'OrderRequest'
        db.delete_table('malawi_orderrequest')

        # Deleting model 'ProductAvailabilityDataSummary'
        db.delete_table('malawi_productavailabilitydatasummary')

        # Deleting model 'ProductAvailabilityData'
        db.delete_table('malawi_productavailabilitydata')

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.location': {
            'Meta': {'object_name': 'Location'},
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
        'logistics.product': {
            'Meta': {'object_name': 'Product'},
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
        'logistics.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.responsibility': {
            'Meta': {'object_name': 'Responsibility'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
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
        'malawi.alert': {
            'Meta': {'object_name': 'Alert'},
            'eo_with_resupply': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'eo_without_resupply': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'have_stockouts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_hsas': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'reporting_receipts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total_requests': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'without_products_managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'malawi.productavailabilitydata': {
            'Meta': {'object_name': 'ProductAvailabilityData'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'good_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
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
            'any_good_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_managed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_over_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_under_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_with_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_without_data': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'any_without_stock': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'malawi.reportingrate': {
            'Meta': {'object_name': 'ReportingRate'},
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
        'malawi.userprofiledata': {
            'Meta': {'object_name': 'UserProfileData'},
            'contact_info': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'contacts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'facility_children': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'hsa_children': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'hsa_supervisors': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_charge': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'last_message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messagelog.Message']", 'null': 'True'}),
            'products_managed': ('django.db.models.fields.TextField', [], {}),
            'supervisor_contacts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"})
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

    complete_apps = ['malawi']