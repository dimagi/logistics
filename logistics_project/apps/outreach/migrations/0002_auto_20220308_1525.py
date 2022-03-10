# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('outreach', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outreachquota',
            name='user',
            field=models.OneToOneField(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
