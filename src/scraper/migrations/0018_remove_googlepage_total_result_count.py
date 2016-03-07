# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0017_auto_20160306_1738'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='googlepage',
            name='total_result_count',
        ),
    ]
