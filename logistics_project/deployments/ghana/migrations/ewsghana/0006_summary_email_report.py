# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from email_reports.models import SchedulableReport, ReportSubscription

class Migration(DataMigration):

    def forwards(self, orm):
        TYPE_HTML = 2
        try:
            SchedulableReport.objects.get(view_name='email-summary')
        except SchedulableReport.DoesNotExist:
            s = SchedulableReport()
            s.view_name = 'email-summary'
            s.display_name = 'Stock Summary'
            s.report_type = TYPE_HTML
            s.save()
        
        rss = ReportSubscription.objects.all()
        for rs in rss:
            view_args = rs.view_args
            if 'location_code' in view_args:
                view_args['place'] = view_args['location_code']
                del view_args['location_code']
            rs.view_args = view_args
            rs.save()

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")


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
