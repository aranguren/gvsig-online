# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2020-02-12 17:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gvsigol_plugin_downloadman', '0023_downloadrequest_generic_request'),
    ]

    operations = [
        migrations.AlterField(
            model_name='downloadrequest',
            name='request_status',
            field=models.CharField(choices=[('RQ', 'Request queued'), ('PR', 'Processing request'), ('CT', 'Completed'), ('CE', 'Completed with errors'), ('RJ', 'Rejected'), ('QE', 'Error queueing request')], db_index=True, default='RQ', max_length=2),
        ),
    ]
