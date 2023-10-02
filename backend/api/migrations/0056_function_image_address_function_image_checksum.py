# Generated by Django 4.1.7 on 2023-10-02 10:00

from django.db import migrations
from django.db import models

import api.models.utils


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0055_rename_function_address_function_archive_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="function",
            name="image_address",
            field=models.URLField(null=True, validators=[api.models.utils.URLValidatorWithOptionalTLD()]),
        ),
        migrations.AddField(
            model_name="function",
            name="image_checksum",
            field=models.CharField(max_length=64, null=True),
        ),
    ]
