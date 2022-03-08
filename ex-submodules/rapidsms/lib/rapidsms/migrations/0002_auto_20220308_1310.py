# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0002_logisticsprofile_organization'),
        ('malawi', '0001_initial'),
        ('rapidsms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='commodities',
            field=models.ManyToManyField(help_text=b'User manages these commodities.', related_name='reported_by', null=True, to='logistics.Product', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contact',
            name='organization',
            field=models.ForeignKey(blank=True, to='malawi.Organization', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contact',
            name='role',
            field=models.ForeignKey(blank=True, to='logistics.ContactRole', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contact',
            name='supply_point',
            field=models.ForeignKey(blank=True, to='logistics.SupplyPoint', null=True),
            preserve_default=True,
        ),
    ]
