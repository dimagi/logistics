# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('malawi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='managed_supply_points',
            field=models.ManyToManyField(to='logistics.SupplyPoint', blank=True),
        ),
    ]
