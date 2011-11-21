# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        db.rename_table('reports_reportsubscription', 'email_reports_reportsubscription')
        db.rename_table('reports_reportsubscription_users', 'email_reports_reportsubscription_users')
        db.rename_table('reports_dailyreportsubscription', 'email_reports_dailyreportsubscription')
        db.rename_table('reports_weeklyreportsubscription', 'email_reports_weeklyreportsubscription')

    def backwards(self, orm):
        
        db.rename_table('email_reports_reportsubscription', 'reports_reportsubscription')
        db.rename_table('email_reports_reportsubscription_users', 'reports_reportsubscription_users')
        db.rename_table('email_reports_dailyreportsubscription', 'reports_dailyreportsubscription')
        db.rename_table('email_reports_weeklyreportsubscription', 'reports_weeklyreportsubscription')

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
        'email_reports.dailyreportsubscription': {
            'Meta': {'object_name': 'DailyReportSubscription', '_ormbases': ['email_reports.ReportSubscription']},
            'hours': ('django.db.models.fields.IntegerField', [], {}),
            'reportsubscription_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['email_reports.ReportSubscription']", 'unique': 'True', 'primary_key': 'True'})
        },
        'email_reports.reportsubscription': {
            'Meta': {'object_name': 'ReportSubscription'},
            '_view_args': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
        'email_reports.weeklyreportsubscription': {
            'Meta': {'object_name': 'WeeklyReportSubscription', '_ormbases': ['email_reports.ReportSubscription']},
            'day_of_week': ('django.db.models.fields.IntegerField', [], {}),
            'hours': ('django.db.models.fields.IntegerField', [], {}),
            'reportsubscription_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['email_reports.ReportSubscription']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['email_reports']
