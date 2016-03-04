# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-03-04 12:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0011_auto_20160303_2227'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='googlesearch',
            name='qdr',
        ),
        migrations.AddField(
            model_name='googlesearch',
            name='cd_max',
            field=models.DateField(blank=True, null=True, verbose_name='date end'),
        ),
        migrations.AddField(
            model_name='googlesearch',
            name='cd_min',
            field=models.DateField(blank=True, null=True, verbose_name='date start'),
        ),
    ]
