# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-02 20:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0002_auto_20160302_2054'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='useragent',
            options={'ordering': ['-date_added']},
        ),
        migrations.RenameField(
            model_name='proxy',
            old_name='last_date_google_ban',
            new_name='date_google_ban',
        ),
        migrations.RenameField(
            model_name='proxy',
            old_name='last_date_online',
            new_name='date_online',
        ),
    ]