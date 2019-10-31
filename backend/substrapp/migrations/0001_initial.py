# Generated by Django 2.1.2 on 2019-03-25 17:51

from django.db import migrations, models
import substrapp.models.algo
import substrapp.models.datamanager
import substrapp.models.model
import substrapp.models.objective


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Algo',
            fields=[
                ('pkhash', models.CharField(blank=True, max_length=64, primary_key=True, serialize=False)),
                ('file', models.FileField(max_length=500, upload_to=substrapp.models.algo.upload_to)),
                ('description', models.FileField(max_length=500, upload_to=substrapp.models.algo.upload_to)),
                ('validated', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='DataManager',
            fields=[
                ('pkhash', models.CharField(blank=True, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=100)),
                ('data_opener', models.FileField(max_length=500, upload_to=substrapp.models.datamanager.upload_to)),
                ('description', models.FileField(max_length=500, upload_to=substrapp.models.datamanager.upload_to)),
                ('validated', models.BooleanField(blank=True, default=False)),
            ],
        ),
        migrations.CreateModel(
            name='DataSample',
            fields=[
                ('pkhash', models.CharField(blank=True, max_length=64, primary_key=True, serialize=False)),
                ('validated', models.BooleanField(default=False)),
                ('path', models.FilePathField(blank=True, max_length=500, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Model',
            fields=[
                ('pkhash', models.CharField(blank=True, max_length=64, primary_key=True, serialize=False)),
                ('validated', models.BooleanField(default=False)),
                ('file', models.FileField(max_length=500, upload_to=substrapp.models.model.upload_to)),
            ],
        ),
        migrations.CreateModel(
            name='Objective',
            fields=[
                ('creation_date', models.DateTimeField(editable=False)),
                ('last_modified', models.DateTimeField(editable=False)),
                ('pkhash', models.CharField(blank=True, max_length=64, primary_key=True, serialize=False)),
                ('validated', models.BooleanField(blank=True, default=False)),
                ('description', models.FileField(blank=True, max_length=500, null=True, upload_to=substrapp.models.objective.upload_to)),
                ('metrics', models.FileField(blank=True, max_length=500, null=True, upload_to=substrapp.models.objective.upload_to)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
