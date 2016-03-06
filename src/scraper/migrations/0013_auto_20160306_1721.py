# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-06 16:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0012_auto_20160304_1308'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlepage',
            name='result_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='googlesearch',
            name='result_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='googlesearch',
            name='q',
            field=models.CharField(max_length=100, verbose_name='search'),
        ),
    ]