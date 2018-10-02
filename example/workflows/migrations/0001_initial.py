# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-02 12:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import functools
import workflows.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Operator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.CharField(default=functools.partial(workflows.utils.make_id_with_prefix, *(), **{'length': 12}), max_length=12, unique=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProviderOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state_version', models.IntegerField(default=0)),
                ('uid', models.CharField(default=functools.partial(workflows.utils.make_id_with_prefix, *(), **{'length': 12}), max_length=12, unique=True)),
                ('type', models.CharField(choices=[('activate', 'activate'), ('modify', 'modify'), ('terminate', 'terminate')], default='activate', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('state', models.CharField(choices=[('start', 'Start'), ('state_1', 'State 1'), ('state_2', 'State 2'), ('end', 'End'), ('state_a', 'State A'), ('state_b', 'State B')], default='start', max_length=16)),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='provider_orders', to='workflows.Operator')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProviderOrderHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('from_state', models.CharField(max_length=20)),
                ('to_state', models.CharField(max_length=20)),
                ('underlying', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='histories', to='workflows.ProviderOrder')),
            ],
            options={
                'ordering': ['timestamp'],
                'get_latest_by': 'timestamp',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OVHActivateOrder',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('workflows.providerorder',),
        ),
        migrations.CreateModel(
            name='SFRActivateOrder',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('workflows.providerorder',),
        ),
    ]
