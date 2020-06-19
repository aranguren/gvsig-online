# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2020-06-19 08:09
from __future__ import unicode_literals

from django.db import migrations, models
import gvsigol_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('gvsigol_core', '0023_auto_20200205_1345'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='logo',
            field=models.ImageField(blank=True, default=gvsigol_core.models.get_default_logo_image, null=True, upload_to='images'),
        ),
        migrations.AddField(
            model_name='project',
            name='logo_link',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]