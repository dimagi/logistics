# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='App',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('module', models.CharField(unique=True, max_length=100)),
                ('active', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Backend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identity', models.CharField(max_length=100)),
                ('backend', models.ForeignKey(to='rapidsms.Backend')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, blank=True)),
                ('language', models.CharField(help_text=b'The language which this contact prefers to communicate in, as a W3C language tag. If this field is left blank, RapidSMS will default to: en-us', max_length=6, blank=True)),
                ('needs_reminders', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_approved', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Logistics Contact',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DeliveryReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=255)),
                ('report_id', models.CharField(help_text=b'Gateway assigned ID', max_length=255)),
                ('number', models.CharField(help_text=b'Destination telephone number', max_length=255)),
                ('report', models.CharField(help_text=b'Actual report text', max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='connection',
            name='contact',
            field=models.ForeignKey(blank=True, to='rapidsms.Contact', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='connection',
            unique_together=set([('backend', 'identity')]),
        ),
    ]
