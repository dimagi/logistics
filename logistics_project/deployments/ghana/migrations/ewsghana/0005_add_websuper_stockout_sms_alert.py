# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from rapidsms.contrib.scheduler.models import EventSchedule, \
    set_weekly_event

class Migration(DataMigration):

    def forwards(self, orm):
        try:
            EventSchedule.objects.get(callback="logistics_project.apps.ewsghana.schedule.stockout_notification_to_web_supers")
        except EventSchedule.DoesNotExist:
            # 2:15 pm on Wednesdays
            set_weekly_event("logistics_project.apps.ewsghana.schedule.stockout_notification_to_web_supers",2,14,6)

    def backwards(self, orm):
        try:
            es = EventSchedule.objects.get(callback="logistics_project.apps.ewsghana.schedule.stockout_notification_to_web_supers")
        except EventSchedule.DoesNotExist:
            pass
        else:
            es.delete()

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
