# Generated by Django 4.0 on 2022-01-11 20:05

import django.core.files.storage
from django.db import migrations
from django.db import models

import substrapp.models.datamanager
import substrapp.models.function


def metric_upload_to(instance, filename) -> str:
    return f"metrics/{instance.key}/{filename}"


class Migration(migrations.Migration):

    dependencies = [
        ("substrapp", "0006_create_compute_task_failure_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="algo",
            name="description",
            field=models.FileField(
                max_length=500,
                storage=django.core.files.storage.FileSystemStorage(),
                upload_to=substrapp.models.function.upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="algo",
            name="file",
            field=models.FileField(
                max_length=500,
                storage=django.core.files.storage.FileSystemStorage(),
                upload_to=substrapp.models.function.upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="computetaskfailurereport",
            name="compute_task_key",
            field=models.UUIDField(editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="datamanager",
            name="data_opener",
            field=models.FileField(
                max_length=500,
                storage=django.core.files.storage.FileSystemStorage(),
                upload_to=substrapp.models.datamanager.upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="datamanager",
            name="description",
            field=models.FileField(
                max_length=500,
                storage=django.core.files.storage.FileSystemStorage(),
                upload_to=substrapp.models.datamanager.upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="metric",
            name="address",
            field=models.FileField(
                blank=True,
                max_length=500,
                null=True,
                storage=django.core.files.storage.FileSystemStorage(),
                upload_to=metric_upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="metric",
            name="description",
            field=models.FileField(
                blank=True,
                max_length=500,
                null=True,
                storage=django.core.files.storage.FileSystemStorage(),
                upload_to=metric_upload_to,
            ),
        ),
    ]
