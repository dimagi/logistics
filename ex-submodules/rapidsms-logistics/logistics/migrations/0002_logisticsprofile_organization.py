# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('malawi', '0001_initial'),
        ('logistics', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='logisticsprofile',
            name='organization',
            field=models.ForeignKey(on_delete=models.CASCADE, blank=True, to='malawi.Organization', null=True),
            preserve_default=True,
        ),
    ]
