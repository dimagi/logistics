# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'ContactDetail'
        db.delete_table('ilsgateway_contactdetail')

        # Deleting field 'ServiceDeliveryPoint.service_delivery_point_type'
        db.delete_column('ilsgateway_servicedeliverypoint', 'service_delivery_point_type_id')


    def backwards(self, orm):
        
        # Adding model 'ContactDetail'
        db.create_table('ilsgateway_contactdetail', (
            ('contact_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['rapidsms.Contact'], unique=True, primary_key=True)),
            ('service_delivery_point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPoint'], null=True, blank=True)),
            ('primary', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ContactRole'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
        ))
        db.send_create_signal('ilsgateway', ['ContactDetail'])

        # We cannot add back in field 'ServiceDeliveryPoint.service_delivery_point_type'
        raise RuntimeError(
            "Cannot reverse this migration. 'ServiceDeliveryPoint.service_delivery_point_type' and its values cannot be restored.")


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ilsgateway.contactrole': {
            'Meta': {'object_name': 'ContactRole'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'ilsgateway.deliverygroup': {
            'Meta': {'ordering': "('name',)", 'object_name': 'DeliveryGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'ilsgateway.district': {
            'Meta': {'object_name': 'District', '_ormbases': ['ilsgateway.ServiceDeliveryPoint']},
            'servicedeliverypoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']", 'unique': 'True', 'primary_key': 'True'})
        },
        'ilsgateway.facility': {
            'Meta': {'object_name': 'Facility', '_ormbases': ['ilsgateway.ServiceDeliveryPoint']},
            'servicedeliverypoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']", 'unique': 'True', 'primary_key': 'True'})
        },
        'ilsgateway.ministryofhealth': {
            'Meta': {'object_name': 'MinistryOfHealth', '_ormbases': ['ilsgateway.ServiceDeliveryPoint']},
            'servicedeliverypoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']", 'unique': 'True', 'primary_key': 'True'})
        },
        'ilsgateway.product': {
            'Meta': {'object_name': 'Product'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'product_code': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sms_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ilsgateway.productreporttype': {
            'Meta': {'object_name': 'ProductReportType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sms_code': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'ilsgateway.region': {
            'Meta': {'object_name': 'Region', '_ormbases': ['ilsgateway.ServiceDeliveryPoint']},
            'servicedeliverypoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']", 'unique': 'True', 'primary_key': 'True'})
        },
        'ilsgateway.servicedeliverypoint': {
            'Meta': {'object_name': 'ServiceDeliveryPoint'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delivery_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.DeliveryGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msd_code': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['ilsgateway.Product']", 'through': "orm['ilsgateway.ServiceDeliveryPointProductReport']", 'symmetrical': 'False'})
        },
        'ilsgateway.servicedeliverypointproductreport': {
            'Meta': {'ordering': "('-report_date',)", 'object_name': 'ServiceDeliveryPointProductReport'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messagelog.Message']"}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.Product']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'report_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 10, 2, 10, 37, 44, 169000)', 'auto_now_add': 'True', 'blank': 'True'}),
            'report_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ProductReportType']"}),
            'service_delivery_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']"})
        },
        'ilsgateway.servicedeliverypointstatus': {
            'Meta': {'ordering': "('-status_date',)", 'object_name': 'ServiceDeliveryPointStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service_delivery_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']"}),
            'status_date': ('django.db.models.fields.DateTimeField', [], {}),
            'status_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPointStatusType']"})
        },
        'ilsgateway.servicedeliverypointstatustype': {
            'Meta': {'object_name': 'ServiceDeliveryPointStatusType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ilsgateway.servicedeliverypointtype': {
            'Meta': {'object_name': 'ServiceDeliveryPointType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
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
            'Meta': {'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['ilsgateway']
