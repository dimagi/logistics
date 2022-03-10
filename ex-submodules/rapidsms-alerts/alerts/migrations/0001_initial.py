# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uid', models.CharField(max_length=256)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('escalated_on', models.DateTimeField()),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('text', models.TextField()),
                ('url', models.TextField(null=True, blank=True)),
                ('alert_type', models.CharField(max_length=256)),
                ('is_open', models.BooleanField(default=True)),
                ('escalation_level', models.CharField(max_length=100)),
                ('originating_location', models.ForeignKey(on_delete=models.CASCADE, blank=True, to='locations.Location', null=True)),
                ('owner', models.ForeignKey(on_delete=models.CASCADE, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NotificationComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('text', models.TextField()),
                ('notification', models.ForeignKey(on_delete=models.CASCADE, related_name='comments', to='alerts.Notification')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NotificationVisibility',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('esc_level', models.CharField(max_length=100)),
                ('notif', models.ForeignKey(on_delete=models.CASCADE, related_name='visible_to', to='alerts.Notification')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='alerts_visible', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
