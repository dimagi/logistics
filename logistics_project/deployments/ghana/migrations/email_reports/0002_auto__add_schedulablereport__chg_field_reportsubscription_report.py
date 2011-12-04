# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SchedulableReport'
        db.create_table('email_reports_schedulablereport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('view_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('email_reports', ['SchedulableReport'])

        if not db.dry_run:
            # 1 create the appropriate scheduled reports
            orm.SchedulableReport.objects.get_or_create(view_name="aggregate",
                                                    display_name="Aggregate Stock")
            orm.SchedulableReport.objects.get_or_create(view_name="reporting",
                                                    display_name="SMS Reporting Rates")
            # 2 create the new field, not required
            db.add_column('email_reports_reportsubscription', 'reportfk', 
                          self.gf('django.db.models.fields.related.ForeignKey')\
                          (default=1, to=orm['email_reports.SchedulableReport'], null=True), keep_default=False)
            # 3 on the basis of one, populate the other
            from email_reports.models import SchedulableReport
            for subsc in orm.ReportSubscription.objects.all().order_by('pk'):
                try:
                    report = orm.SchedulableReport.objects.get(view_name=subsc.report)
                except SchedulableReport.DoesNotExist:
                    raise RuntimeError("Old report subscription cannot be mapped to new SchedulableReports")
                    pass
                else:
                    subsc.reportfk = report
                    subsc.save()
        db.delete_column('email_reports_reportsubscription', 'report')

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")

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
            'report': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'reportfk': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['email_reports.SchedulableReport']", 'null': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
        'email_reports.schedulablereport': {
            'Meta': {'object_name': 'SchedulableReport'},
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'view_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'email_reports.weeklyreportsubscription': {
            'Meta': {'object_name': 'WeeklyReportSubscription', '_ormbases': ['email_reports.ReportSubscription']},
            'day_of_week': ('django.db.models.fields.IntegerField', [], {}),
            'hours': ('django.db.models.fields.IntegerField', [], {}),
            'reportsubscription_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['email_reports.ReportSubscription']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['email_reports']
