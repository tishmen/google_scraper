# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-06 16:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0014_googlepage_estimated_result_count'),
    ]

    operations = [
        migrations.RenameField(
            model_name='googlepage',
            old_name='estimated_result_count',
            new_name='total_result_count',
        ),
    ]
