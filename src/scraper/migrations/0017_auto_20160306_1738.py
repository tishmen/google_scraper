# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-06 16:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0016_auto_20160306_1737'),
    ]

    operations = [
        migrations.AlterField(
            model_name='googlepage',
            name='end',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='googlepage',
            name='start',
            field=models.PositiveIntegerField(),
        ),
    ]
