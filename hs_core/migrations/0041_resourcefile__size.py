# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-02-21 22:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0040_auto_20190105_1844'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='_size',
            field=models.BigIntegerField(default=0),
        ),
    ]
