# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-27 18:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20161027_1656'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='date_accessed',
            field=models.DateField(auto_now=True),
        ),
    ]