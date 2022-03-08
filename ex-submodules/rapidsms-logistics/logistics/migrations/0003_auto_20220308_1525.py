# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0002_logisticsprofile_organization'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='defaultmonthlyconsumption',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='defaultmonthlyconsumption',
            name='product',
        ),
        migrations.RemoveField(
            model_name='defaultmonthlyconsumption',
            name='supply_point_type',
        ),
        migrations.RemoveField(
            model_name='contactrole',
            name='responsibilities',
        ),
        migrations.RemoveField(
            model_name='product',
            name='equivalents',
        ),
        migrations.RemoveField(
            model_name='supplypoint',
            name='groups',
        ),
        migrations.RemoveField(
            model_name='supplypointtype',
            name='default_monthly_consumptions',
        ),
        migrations.AlterField(
            model_name='logisticsprofile',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='DefaultMonthlyConsumption',
        ),
        migrations.DeleteModel(
            name='Responsibility',
        ),
        migrations.DeleteModel(
            name='SupplyPointGroup',
        ),
    ]
