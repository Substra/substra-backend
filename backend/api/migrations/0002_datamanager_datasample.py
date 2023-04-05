# Generated by Django 4.0 on 2022-01-21 16:33

import django.contrib.postgres.fields
from django.db import migrations
from django.db import models

import api.models.utils


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataManager",
            fields=[
                ("key", models.UUIDField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                (
                    "description_address",
                    models.URLField(validators=[api.models.utils.URLValidatorWithOptionalTLD()]),
                ),
                ("description_checksum", models.CharField(max_length=64)),
                ("opener_address", models.URLField(validators=[api.models.utils.URLValidatorWithOptionalTLD()])),
                ("opener_checksum", models.CharField(max_length=64)),
                ("permissions_download_public", models.BooleanField()),
                (
                    "permissions_download_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), size=100),
                ),
                ("permissions_process_public", models.BooleanField()),
                (
                    "permissions_process_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), size=100),
                ),
                ("logs_permission_public", models.BooleanField()),
                (
                    "logs_permission_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), size=100),
                ),
                ("type", models.CharField(max_length=100)),
                ("owner", models.CharField(max_length=100)),
                ("creation_date", models.DateTimeField()),
                ("metadata", models.JSONField()),
                ("channel", models.CharField(max_length=100)),
            ],
            options={
                "ordering": ["creation_date", "key"],
            },
        ),
        migrations.CreateModel(
            name="DataSample",
            fields=[
                ("key", models.UUIDField(primary_key=True, serialize=False)),
                ("owner", models.CharField(max_length=100)),
                ("creation_date", models.DateTimeField()),
                ("channel", models.CharField(max_length=100)),
                ("test_only", models.BooleanField()),
                (
                    "data_managers",
                    models.ManyToManyField(
                        related_name="data_samples", related_query_name="data_sample", to="api.DataManager"
                    ),
                ),
            ],
            options={
                "ordering": ["creation_date", "key"],
            },
        ),
    ]
