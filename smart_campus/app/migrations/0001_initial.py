# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-11 12:46
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=255, primary_key=True, serialize=False, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('nickname', models.CharField(blank=True, max_length=254)),
                ('experience_point', models.IntegerField(default=0)),
                ('earned_coins', models.IntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Beacon',
            fields=[
                ('beacon_id', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('location', django.contrib.gis.db.models.fields.GeometryField(null=True, srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=254)),
                ('question_type', models.IntegerField(choices=[(1, 'True or False'), (2, 'MuitipleChoice')], default=2)),
            ],
        ),
        migrations.CreateModel(
            name='QuestionChoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_answer', models.BooleanField(default=False)),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Choice')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Question')),
            ],
        ),
        migrations.CreateModel(
            name='Reward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('image', models.ImageField(null=True, upload_to='images/reward/')),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
                ('permissions', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=254, unique=True)),
                ('content', models.TextField(blank=True)),
                ('location', django.contrib.gis.db.models.fields.GeometryField(null=True, srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='StationCategory',
            fields=[
                ('name', models.CharField(max_length=254, primary_key=True, serialize=False)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='StationImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='images/station/')),
                ('is_primary', models.BooleanField(default=False)),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Station')),
            ],
        ),
        migrations.CreateModel(
            name='TravelPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=254)),
                ('description', models.TextField(blank=True)),
                ('travel_time', models.CharField(max_length=50)),
                ('stations', models.ManyToManyField(to='app.Station')),
            ],
        ),
        migrations.CreateModel(
            name='UserGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserReward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('reward', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Reward')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='station',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.StationCategory'),
        ),
        migrations.AddField(
            model_name='station',
            name='owner_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.UserGroup'),
        ),
        migrations.AddField(
            model_name='question',
            name='choices',
            field=models.ManyToManyField(through='app.QuestionChoice', to='app.Choice'),
        ),
        migrations.AddField(
            model_name='question',
            name='linked_station',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Station'),
        ),
        migrations.AddField(
            model_name='beacon',
            name='owner_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.UserGroup'),
        ),
        migrations.AddField(
            model_name='beacon',
            name='station',
            field=models.ManyToManyField(to='app.Station'),
        ),
        migrations.AddField(
            model_name='user',
            name='answered_questions',
            field=models.ManyToManyField(to='app.Question'),
        ),
        migrations.AddField(
            model_name='user',
            name='favorite_stations',
            field=models.ManyToManyField(to='app.Station'),
        ),
        migrations.AddField(
            model_name='user',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.UserGroup'),
        ),
        migrations.AddField(
            model_name='user',
            name='received_rewards',
            field=models.ManyToManyField(through='app.UserReward', to='app.Reward'),
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Role'),
        ),
        migrations.AddField(
            model_name='user',
            name='visited_beacons',
            field=models.ManyToManyField(to='app.Beacon'),
        ),
    ]
