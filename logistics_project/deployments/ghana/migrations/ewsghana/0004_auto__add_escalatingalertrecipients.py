# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'EscalatingAlertRecipients'
        db.create_table('ewsghana_escalatingalertrecipients', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.LocationType'])),
            ('program', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['logistics.ProductType'], null=True, blank=True)),
        ))
        db.send_create_signal('ewsghana', ['EscalatingAlertRecipients'])


    def backwards(self, orm):
        
        # Deleting model 'EscalatingAlertRecipients'
        db.delete_table('ewsghana_escalatingalertrecipients')


    models = {
        'ewsghana.escalatingalertrecipients': {
            'Meta': {'object_name': 'EscalatingAlertRecipients'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.LocationType']"}),
            'program': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logistics.ProductType']", 'null': 'True', 'blank': 'True'})
        },
        'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'display_order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True', 'db_index': 'True'})
        },
        'logistics.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['ewsghana']
