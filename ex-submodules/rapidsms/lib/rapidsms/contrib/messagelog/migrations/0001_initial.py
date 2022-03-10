# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('rapidsms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('direction', models.CharField(max_length=1, choices=[(b'I', b'Incoming'), (b'O', b'Outgoing')])),
                ('date', models.DateTimeField()),
                ('text', models.TextField()),
                ('connection', models.ForeignKey(on_delete=models.CASCADE, to='rapidsms.Connection', null=True)),
                ('contact', models.ForeignKey(on_delete=models.CASCADE, to='rapidsms.Contact', null=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
