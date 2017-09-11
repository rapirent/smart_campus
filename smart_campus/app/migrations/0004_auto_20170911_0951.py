# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-11 09:51
from __future__ import unicode_literals

import app.models
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20170911_0936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stationimage',
            name='image',
            field=models.ImageField(storage=django.core.files.storage.FileSystemStorage(base_url='/media/station/', location='/home/kuoteng/smart_campus/smart_campus/smart_campus/media/station/'), upload_to=app.models.image_directory_path),
        ),
    ]