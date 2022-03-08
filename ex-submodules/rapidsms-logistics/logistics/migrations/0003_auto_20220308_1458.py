# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0002_logisticsprofile_organization'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contactrole',
            name='responsibilities',
        ),
        migrations.DeleteModel(
            name='Responsibility',
        ),
    ]
