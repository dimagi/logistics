# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OutreachMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('sent_by', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OutreachQuota',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.PositiveIntegerField(default=5)),
                ('user', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
