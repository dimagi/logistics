# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rapidsms', '0002_auto_20220308_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='commodities',
            field=models.ManyToManyField(help_text=b'User manages these commodities.', related_name='reported_by', to='logistics.Product', blank=True),
        ),
    ]
