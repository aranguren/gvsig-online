# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-03 11:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gvsigol_plugin_sampledashboard', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sampledashboard',
            old_name='titulo',
            new_name='title',
        ),
    ]
