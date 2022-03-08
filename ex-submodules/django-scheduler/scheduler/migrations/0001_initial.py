# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import scheduler.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EventSchedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('callback', models.CharField(help_text=b'Name of Python callback function', max_length=255)),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('callback_args', scheduler.fields.JSONField(null=True, blank=True)),
                ('callback_kwargs', scheduler.fields.JSONField(null=True, blank=True)),
                ('months', scheduler.fields.JSONField(help_text=b"'1,2,3' for jan, feb, march - '*' for all", null=True, blank=True)),
                ('days_of_month', scheduler.fields.JSONField(help_text=b"'1,2,3' for 1st, 2nd, 3rd - '*' for all", null=True, blank=True)),
                ('days_of_week', scheduler.fields.JSONField(help_text=b"'0,1,2' for mon, tue, wed - '*' for all", null=True, blank=True)),
                ('hours', scheduler.fields.JSONField(help_text=b"'0,1,2' for midnight, 1 o'clock, 2 - '*' for all", null=True, blank=True)),
                ('minutes', scheduler.fields.JSONField(help_text=b"'0,1,2' for X:00, X:01, X:02 - '*' for all", null=True, blank=True)),
                ('start_time', models.DateTimeField(help_text=b"When do you want alerts to start? Leave blank for 'now'.", null=True, blank=True)),
                ('end_time', models.DateTimeField(help_text=b"When do you want alerts to end? Leave blank for 'never'.", null=True, blank=True)),
                ('last_ran', models.DateTimeField(null=True, blank=True)),
                ('count', models.IntegerField(help_text=b"How many times do you want this to fire? Leave blank for 'continuously'", null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExecutionRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('runtime', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FailedExecutionRecord',
            fields=[
                ('executionrecord_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='scheduler.ExecutionRecord')),
                ('message', models.TextField()),
            ],
            options={
            },
            bases=('scheduler.executionrecord',),
        ),
        migrations.AddField(
            model_name='executionrecord',
            name='schedule',
            field=models.ForeignKey(to='scheduler.EventSchedule'),
            preserve_default=True,
        ),
    ]
