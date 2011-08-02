# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'NodeType'
        db.delete_table('ilsgateway_nodetype')

        # Deleting model 'Node'
        db.delete_table('ilsgateway_node')

        # Deleting model 'NodeStatusType'
        db.delete_table('ilsgateway_nodestatustype')

        # Deleting model 'NodeStatus'
        db.delete_table('ilsgateway_nodestatus')

        # Deleting model 'NodeProductReport'
        db.delete_table('ilsgateway_nodeproductreport')

        # Deleting model 'NodeLocation'
        db.delete_table('ilsgateway_nodelocation')

        # Adding model 'ServiceDeliveryPointLocation'
        db.create_table('ilsgateway_servicedeliverypointlocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Point'], null=True, blank=True)),
            ('parent_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('parent_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('sdp', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPoint'], null=True, blank=True)),
        ))
        db.send_create_signal('ilsgateway', ['ServiceDeliveryPointLocation'])

        # Adding model 'ServiceDeliveryPoint'
        db.create_table('ilsgateway_servicedeliverypoint', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sdp_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPointType'], null=True, blank=True)),
            ('parent_sdp', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPoint'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('delivery_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.DeliveryGroup'], null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('msd_code', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('ilsgateway', ['ServiceDeliveryPoint'])

        # Adding model 'ServiceDeliveryPointType'
        db.create_table('ilsgateway_servicedeliverypointtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('parent_sdp_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPointType'], null=True, blank=True)),
        ))
        db.send_create_signal('ilsgateway', ['ServiceDeliveryPointType'])

        # Adding model 'ServiceDeliveryPointStatusType'
        db.create_table('ilsgateway_servicedeliverypointstatustype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('ilsgateway', ['ServiceDeliveryPointStatusType'])

        # Adding model 'ServiceDeliveryPointProductReport'
        db.create_table('ilsgateway_servicedeliverypointproductreport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.Product'])),
            ('sdp', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPoint'])),
            ('report_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ProductReportType'])),
            ('quantity', self.gf('django.db.models.fields.IntegerField')()),
            ('report_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2010, 9, 8, 15, 48, 12, 889000), auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('ilsgateway', ['ServiceDeliveryPointProductReport'])

        # Adding model 'ServiceDeliveryPointStatus'
        db.create_table('ilsgateway_servicedeliverypointstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPointStatusType'])),
            ('status_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('sdp', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPoint'])),
        ))
        db.send_create_signal('ilsgateway', ['ServiceDeliveryPointStatus'])

        # Deleting field 'ContactDetail.node'
        db.delete_column('ilsgateway_contactdetail', 'node_id')

        # Adding field 'ContactDetail.sdp'
        db.add_column('ilsgateway_contactdetail', 'sdp', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ServiceDeliveryPoint'], null=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'NodeType'
        db.create_table('ilsgateway_nodetype', (
            ('parent_node_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.NodeType'], null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('ilsgateway', ['NodeType'])

        # Adding model 'Node'
        db.create_table('ilsgateway_node', (
            ('node_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.NodeType'], null=True, blank=True)),
            ('msd_code', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('parent_node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.Node'], null=True, blank=True)),
            ('delivery_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.DeliveryGroup'], null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('ilsgateway', ['Node'])

        # Adding model 'NodeStatusType'
        db.create_table('ilsgateway_nodestatustype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('ilsgateway', ['NodeStatusType'])

        # Adding model 'NodeStatus'
        db.create_table('ilsgateway_nodestatus', (
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.Node'])),
            ('status_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.NodeStatusType'])),
        ))
        db.send_create_signal('ilsgateway', ['NodeStatus'])

        # Adding model 'NodeProductReport'
        db.create_table('ilsgateway_nodeproductreport', (
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.Node'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.Product'])),
            ('report_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2010, 9, 2, 20, 20, 17, 88000), auto_now_add=True, blank=True)),
            ('report_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.ProductReportType'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('ilsgateway', ['NodeProductReport'])

        # Adding model 'NodeLocation'
        db.create_table('ilsgateway_nodelocation', (
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.Node'], null=True, blank=True)),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Point'], null=True, blank=True)),
            ('parent_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('parent_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('ilsgateway', ['NodeLocation'])

        # Deleting model 'ServiceDeliveryPointLocation'
        db.delete_table('ilsgateway_servicedeliverypointlocation')

        # Deleting model 'ServiceDeliveryPoint'
        db.delete_table('ilsgateway_servicedeliverypoint')

        # Deleting model 'ServiceDeliveryPointType'
        db.delete_table('ilsgateway_servicedeliverypointtype')

        # Deleting model 'ServiceDeliveryPointStatusType'
        db.delete_table('ilsgateway_servicedeliverypointstatustype')

        # Deleting model 'ServiceDeliveryPointProductReport'
        db.delete_table('ilsgateway_servicedeliverypointproductreport')

        # Deleting model 'ServiceDeliveryPointStatus'
        db.delete_table('ilsgateway_servicedeliverypointstatus')

        # Adding field 'ContactDetail.node'
        db.add_column('ilsgateway_contactdetail', 'node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ilsgateway.Node'], null=True), keep_default=False)

        # Deleting field 'ContactDetail.sdp'
        db.delete_column('ilsgateway_contactdetail', 'sdp_id')


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
        'ilsgateway.contactdetail': {
            'Meta': {'object_name': 'ContactDetail'},
            'contact': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['rapidsms.Contact']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'primary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ContactRole']", 'null': 'True', 'blank': 'True'}),
            'sdp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'ilsgateway.contactrole': {
            'Meta': {'object_name': 'ContactRole'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'ilsgateway.deliverygroup': {
            'Meta': {'ordering': "('name',)", 'object_name': 'DeliveryGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        'ilsgateway.servicedeliverypoint': {
            'Meta': {'object_name': 'ServiceDeliveryPoint'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delivery_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.DeliveryGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msd_code': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'parent_sdp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']", 'null': 'True', 'blank': 'True'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['ilsgateway.Product']", 'through': "orm['ilsgateway.ServiceDeliveryPointProductReport']", 'symmetrical': 'False'}),
            'sdp_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPointType']", 'null': 'True', 'blank': 'True'})
        },
        'ilsgateway.servicedeliverypointlocation': {
            'Meta': {'object_name': 'ServiceDeliveryPointLocation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'sdp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']", 'null': 'True', 'blank': 'True'})
        },
        'ilsgateway.servicedeliverypointproductreport': {
            'Meta': {'ordering': "('-report_date',)", 'object_name': 'ServiceDeliveryPointProductReport'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.Product']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'report_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 9, 8, 15, 48, 12, 889000)', 'auto_now_add': 'True', 'blank': 'True'}),
            'report_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ProductReportType']"}),
            'sdp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']"})
        },
        'ilsgateway.servicedeliverypointstatus': {
            'Meta': {'ordering': "('-status_date',)", 'object_name': 'ServiceDeliveryPointStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sdp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPoint']"}),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'parent_sdp_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ilsgateway.ServiceDeliveryPointType']", 'null': 'True', 'blank': 'True'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['ilsgateway']
