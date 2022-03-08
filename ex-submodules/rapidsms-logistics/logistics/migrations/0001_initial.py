# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings
import logistics.mixin


class Migration(migrations.Migration):

    dependencies = [
        ('messagelog', '0001_initial'),
        ('locations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rapidsms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=30)),
                ('name', models.CharField(max_length=100, blank=True)),
            ],
            options={
                'verbose_name': 'Role',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DefaultMonthlyConsumption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('default_monthly_consumption', models.PositiveIntegerField(default=None, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HistoricalStockCache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.PositiveIntegerField()),
                ('month', models.PositiveIntegerField()),
                ('stock', models.IntegerField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LogisticsProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('designation', models.CharField(max_length=255, null=True, blank=True)),
                ('can_view_hsa_level_data', models.BooleanField(default=True)),
                ('can_view_facility_level_data', models.BooleanField(default=False)),
                ('current_dashboard_base_level', models.CharField(default=b'h', max_length=1)),
                ('location', models.ForeignKey(blank=True, to='locations.Location', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NagRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('report_date', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('warning', models.IntegerField(default=1)),
                ('nag_type', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('units', models.CharField(max_length=100)),
                ('sms_code', models.CharField(unique=True, max_length=10, db_index=True)),
                ('description', models.CharField(max_length=255)),
                ('product_code', models.CharField(db_index=True, max_length=100, null=True, blank=True)),
                ('average_monthly_consumption', models.PositiveIntegerField(null=True, blank=True)),
                ('emergency_order_level', models.PositiveIntegerField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('equivalents', models.ManyToManyField(related_name='equivalents_rel_+', null=True, to='logistics.Product', blank=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField()),
                ('report_date', models.DateTimeField(default=datetime.datetime.utcnow, db_index=True)),
                ('message', models.ForeignKey(blank=True, to='messagelog.Message', null=True)),
                ('product', models.ForeignKey(to='logistics.Product')),
            ],
            options={
                'verbose_name': 'Product Report',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductReportType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(unique=True, max_length=10)),
            ],
            options={
                'verbose_name': 'Product Report Type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductStock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('quantity', models.IntegerField(null=True, blank=True)),
                ('days_stocked_out', models.IntegerField(default=0)),
                ('last_modified', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('manual_monthly_consumption', models.PositiveIntegerField(default=None, null=True, blank=True)),
                ('auto_monthly_consumption', models.PositiveIntegerField(default=None, null=True, blank=True)),
                ('use_auto_consumption', models.BooleanField(default=True)),
                ('product', models.ForeignKey(to='logistics.Product')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(unique=True, max_length=10)),
                ('base_level', models.CharField(default=b'h', max_length=1)),
            ],
            options={
                'verbose_name': 'Product Type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Responsibility',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=30)),
                ('name', models.CharField(max_length=100, blank=True)),
            ],
            options={
                'verbose_name': 'Responsibility',
                'verbose_name_plural': 'Responsibilities',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(db_index=True, max_length=20, choices=[(b'requested', b'requested'), (b'approved', b'approved'), (b'stocked_out', b'stocked_out'), (b'partially_stocked', b'partially_stocked'), (b'received', b'received'), (b'canceled', b'canceled')])),
                ('response_status', models.CharField(blank=True, max_length=20, choices=[(b'approved', b'approved'), (b'stocked_out', b'stocked_out'), (b'partially_stocked', b'partially_stocked')])),
                ('is_emergency', models.BooleanField(default=False)),
                ('requested_on', models.DateTimeField()),
                ('responded_on', models.DateTimeField(null=True)),
                ('received_on', models.DateTimeField(null=True)),
                ('balance', models.IntegerField(default=None, null=True)),
                ('amount_requested', models.PositiveIntegerField(null=True)),
                ('amount_approved', models.PositiveIntegerField(null=True)),
                ('amount_received', models.PositiveIntegerField(null=True)),
                ('canceled_for', models.ForeignKey(to='logistics.StockRequest', null=True)),
                ('product', models.ForeignKey(to='logistics.Product')),
                ('received_by', models.ForeignKey(related_name='received_by', to='rapidsms.Contact', null=True)),
                ('requested_by', models.ForeignKey(related_name='requested_by', to='rapidsms.Contact', null=True)),
                ('responded_by', models.ForeignKey(related_name='responded_by', to='rapidsms.Contact', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField()),
                ('beginning_balance', models.IntegerField()),
                ('ending_balance', models.IntegerField()),
                ('date', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('product', models.ForeignKey(to='logistics.Product')),
                ('product_report', models.ForeignKey(to='logistics.ProductReport', null=True)),
            ],
            options={
                'verbose_name': 'Stock Transaction',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockTransfer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('giver_unknown', models.CharField(max_length=200, blank=True)),
                ('amount', models.PositiveIntegerField(null=True, blank=True)),
                ('status', models.CharField(max_length=10, choices=[(b'initiated', b'initiated'), (b'confirmed', b'confirmed'), (b'canceled', b'canceled')])),
                ('initiated_on', models.DateTimeField(null=True, blank=True)),
                ('closed_on', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SupplyPoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('code', models.CharField(unique=True, max_length=100, db_index=True)),
                ('last_reported', models.DateTimeField(default=None, null=True, blank=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model, logistics.mixin.StockCacheMixin),
        ),
        migrations.CreateModel(
            name='SupplyPointGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SupplyPointType',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('code', models.SlugField(unique=True, serialize=False, primary_key=True)),
                ('default_monthly_consumptions', models.ManyToManyField(to='logistics.Product', null=True, through='logistics.DefaultMonthlyConsumption', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SupplyPointWarehouseRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('create_date', models.DateTimeField()),
                ('supply_point', models.ForeignKey(to='logistics.SupplyPoint')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='supplypoint',
            name='groups',
            field=models.ManyToManyField(to='logistics.SupplyPointGroup', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='supplypoint',
            name='location',
            field=models.ForeignKey(to='locations.Location'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='supplypoint',
            name='supplied_by',
            field=models.ForeignKey(blank=True, to='logistics.SupplyPoint', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='supplypoint',
            name='type',
            field=models.ForeignKey(to='logistics.SupplyPointType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='giver',
            field=models.ForeignKey(related_name='giver', blank=True, to='logistics.SupplyPoint', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='product',
            field=models.ForeignKey(to='logistics.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='receiver',
            field=models.ForeignKey(related_name='receiver', to='logistics.SupplyPoint'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='stocktransaction',
            name='supply_point',
            field=models.ForeignKey(to='logistics.SupplyPoint'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='stockrequest',
            name='supply_point',
            field=models.ForeignKey(to='logistics.SupplyPoint'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productstock',
            name='supply_point',
            field=models.ForeignKey(to='logistics.SupplyPoint'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='productstock',
            unique_together=set([('supply_point', 'product')]),
        ),
        migrations.AddField(
            model_name='productreport',
            name='report_type',
            field=models.ForeignKey(to='logistics.ProductReportType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productreport',
            name='supply_point',
            field=models.ForeignKey(to='logistics.SupplyPoint'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='type',
            field=models.ForeignKey(to='logistics.ProductType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nagrecord',
            name='supply_point',
            field=models.ForeignKey(to='logistics.SupplyPoint'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='logisticsprofile',
            name='supply_point',
            field=models.ForeignKey(blank=True, to='logistics.SupplyPoint', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='logisticsprofile',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalstockcache',
            name='product',
            field=models.ForeignKey(to='logistics.Product', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalstockcache',
            name='supply_point',
            field=models.ForeignKey(to='logistics.SupplyPoint'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='defaultmonthlyconsumption',
            name='product',
            field=models.ForeignKey(to='logistics.Product'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='defaultmonthlyconsumption',
            name='supply_point_type',
            field=models.ForeignKey(to='logistics.SupplyPointType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='defaultmonthlyconsumption',
            unique_together=set([('supply_point_type', 'product')]),
        ),
        migrations.AddField(
            model_name='contactrole',
            name='responsibilities',
            field=models.ManyToManyField(to='logistics.Responsibility', null=True, blank=True),
            preserve_default=True,
        ),
    ]
