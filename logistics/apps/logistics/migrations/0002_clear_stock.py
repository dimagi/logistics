# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):
    depends_on = (
        ("rapidsms", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding field 'ProductStock.manual_monthly_consumption'
        db.add_column('logistics_productstock', 'manual_monthly_consumption', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True, blank=True), keep_default=False)
        # Adding field 'ProductStock.auto_monthly_consumption'
        db.add_column('logistics_productstock', 'auto_monthly_consumption', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True, blank=True), keep_default=False)
        # Adding field 'ProductStock.use_auto_consumption'
        db.add_column('logistics_productstock', 'use_auto_consumption', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Clean start on everything stock related
        db.clear_table('logistics_requisitionreport')
        db.clear_table('logistics_stocktransaction')
        # Turns out we should NOT clear product reports, so that we don't send out
        #   nagging reminders after the upgrade
        # db.clear_table('logistics_productreport')
        # we need to persist productstock: specifically, 'consumption'
        # db.clear_table('logistics_productstock')

        # Adding model 'SupplyPointType'
        db.create_table('logistics_supplypointtype', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, primary_key=True, db_index=True)),
        ))
        db.send_create_signal('logistics', ['SupplyPointType'])

        # Adding model 'SupplyPoint'
        db.create_table('logistics_supplypoint', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPointType'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('last_reported', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Location'])),
            ('supplied_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.SupplyPoint'], null=True, blank=True)),
        ))
        db.send_create_signal('logistics', ['SupplyPoint'])

    def backwards(self, orm):
        # We cannot add back in field 'ProductReport.facility'
        raise RuntimeError(
            "Stocks were destructively cleared. There is no way back.")

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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
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
            'Meta': {'object_name': 'Location'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
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
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True', 'db_index': 'True'})
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
        'logistics.facility': {
            'Meta': {'object_name': 'Facility', '_ormbases': ['logistics.SupplyPoint']},
            'supplypoint_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['logistics.SupplyPoint']", 'unique': 'True', 'primary_key': 'True'})
        },
        'logistics.logisticsprofile': {
            'Meta': {'object_name': 'LogisticsProfile'},
            'facility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Facility']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'logistics.product': {
            'Meta': {'object_name': 'Product'},
            'average_monthly_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'product_code': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sms_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ProductType']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.productreport': {
            'Meta': {'ordering': "('-report_date',)", 'object_name': 'ProductReport'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messagelog.Message']", 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'report_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'manual_monthly_consumption': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"}),
            'use_auto_consumption': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'logistics.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logistics.requisitionreport': {
            'Meta': {'ordering': "('-report_date',)", 'object_name': 'RequisitionReport'},
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
        'logistics.stocktransaction': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'StockTransaction'},
            'beginning_balance': ('django.db.models.fields.IntegerField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'ending_balance': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.Product']"}),
            'product_report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ProductReport']", 'null': 'True'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']"})
        },
        'logistics.supplypoint': {
            'Meta': {'object_name': 'SupplyPoint'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_reported': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'supplied_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPointType']"})
        },
        'logistics.supplypointtype': {
            'Meta': {'object_name': 'SupplyPointType'},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'needs_reminders': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ContactRole']", 'null': 'True', 'blank': 'True'}),
            'supply_point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.SupplyPoint']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['logistics']
