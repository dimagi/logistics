# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rapidsms', '0001_initial'),
        ('logistics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_hsas', models.PositiveIntegerField(default=0)),
                ('have_stockouts', models.PositiveIntegerField(default=0)),
                ('eo_total', models.PositiveIntegerField(default=0)),
                ('eo_with_resupply', models.PositiveIntegerField(default=0)),
                ('eo_without_resupply', models.PositiveIntegerField(default=0)),
                ('total_requests', models.PositiveIntegerField(default=0)),
                ('reporting_receipts', models.PositiveIntegerField(default=0)),
                ('order_readys', models.PositiveIntegerField(default=0)),
                ('without_products_managed', models.PositiveIntegerField(default=0)),
                ('products_requested', models.PositiveIntegerField(default=0)),
                ('products_approved', models.PositiveIntegerField(default=0)),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CalculatedConsumption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('date', models.DateTimeField()),
                ('calculated_consumption', models.PositiveIntegerField(default=0)),
                ('time_with_data', models.BigIntegerField(default=0)),
                ('time_needing_data', models.BigIntegerField(default=0)),
                ('time_stocked_out', models.BigIntegerField(default=0)),
                ('product', models.ForeignKey(to='logistics.Product')),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CurrentConsumption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('total', models.PositiveIntegerField(default=0)),
                ('current_daily_consumption', models.FloatField(default=0)),
                ('stock_on_hand', models.BigIntegerField(default=0)),
                ('product', models.ForeignKey(to='logistics.Product')),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HistoricalStock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('date', models.DateTimeField()),
                ('stock', models.BigIntegerField(default=0)),
                ('total', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(to='logistics.Product')),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderFulfillment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('date', models.DateTimeField()),
                ('total', models.PositiveIntegerField(default=0)),
                ('quantity_requested', models.PositiveIntegerField(default=0)),
                ('quantity_received', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(to='logistics.Product')),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrderRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('date', models.DateTimeField()),
                ('total', models.PositiveIntegerField(default=0)),
                ('emergency', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(to='logistics.Product')),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('managed_supply_points', models.ManyToManyField(to='logistics.SupplyPoint', null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAvailabilityData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('date', models.DateTimeField()),
                ('total', models.PositiveIntegerField(default=0)),
                ('managed', models.PositiveIntegerField(default=0)),
                ('with_stock', models.PositiveIntegerField(default=0)),
                ('under_stock', models.PositiveIntegerField(default=0)),
                ('good_stock', models.PositiveIntegerField(default=0)),
                ('over_stock', models.PositiveIntegerField(default=0)),
                ('without_stock', models.PositiveIntegerField(default=0)),
                ('without_data', models.PositiveIntegerField(default=0)),
                ('emergency_stock', models.PositiveIntegerField(default=0)),
                ('managed_and_with_stock', models.PositiveIntegerField(default=0)),
                ('managed_and_under_stock', models.PositiveIntegerField(default=0)),
                ('managed_and_good_stock', models.PositiveIntegerField(default=0)),
                ('managed_and_over_stock', models.PositiveIntegerField(default=0)),
                ('managed_and_without_stock', models.PositiveIntegerField(default=0)),
                ('managed_and_without_data', models.PositiveIntegerField(default=0)),
                ('managed_and_emergency_stock', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(to='logistics.Product')),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAvailabilityDataSummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('date', models.DateTimeField()),
                ('total', models.PositiveIntegerField(default=0)),
                ('any_managed', models.PositiveIntegerField(default=0)),
                ('any_without_stock', models.PositiveIntegerField(default=0)),
                ('any_with_stock', models.PositiveIntegerField(default=0)),
                ('any_under_stock', models.PositiveIntegerField(default=0)),
                ('any_over_stock', models.PositiveIntegerField(default=0)),
                ('any_good_stock', models.PositiveIntegerField(default=0)),
                ('any_without_data', models.PositiveIntegerField(default=0)),
                ('any_emergency_stock', models.PositiveIntegerField(default=0)),
                ('base_level', models.CharField(default=b'h', max_length=1)),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RefrigeratorMalfunction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reported_on', models.DateTimeField(db_index=True)),
                ('malfunction_reason', models.CharField(max_length=1)),
                ('responded_on', models.DateTimeField(null=True)),
                ('resolved_on', models.DateTimeField(null=True)),
                ('reported_by', models.ForeignKey(related_name='+', to='rapidsms.Contact')),
                ('sent_to', models.ForeignKey(related_name='+', to='logistics.SupplyPoint', null=True)),
                ('supply_point', models.ForeignKey(related_name='+', to='logistics.SupplyPoint')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReportingRate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('date', models.DateTimeField()),
                ('total', models.PositiveIntegerField(default=0)),
                ('reported', models.PositiveIntegerField(default=0)),
                ('on_time', models.PositiveIntegerField(default=0)),
                ('complete', models.PositiveIntegerField(default=0)),
                ('base_level', models.CharField(default=b'h', max_length=1)),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TimeTracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField(editable=False)),
                ('update_date', models.DateTimeField(editable=False)),
                ('date', models.DateTimeField()),
                ('type', models.CharField(max_length=10, choices=[(b'ord-ready', b'order - ready'), (b'ready-rec', b'ready - received')])),
                ('total', models.PositiveIntegerField(default=0)),
                ('time_in_seconds', models.BigIntegerField(default=0)),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
