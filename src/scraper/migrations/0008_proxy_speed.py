# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-02 21:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0007_auto_20160302_2209'),
    ]

    operations = [
        migrations.AddField(
            model_name='proxy',
            name='speed',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
