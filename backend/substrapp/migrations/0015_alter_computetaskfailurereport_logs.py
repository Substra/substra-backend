# Generated by Django 4.1.7 on 2023-08-10 08:43

from django.db import migrations
from django.db import models

import substrapp.models.asset_failure_report
import substrapp.storages.minio


class Migration(migrations.Migration):
    dependencies = [
        ("substrapp", "0014_rename_algo_to_function"),
    ]

    operations = [
        migrations.AlterField(
            model_name="computetaskfailurereport",
            name="logs",
            field=models.FileField(
                max_length=36,
                storage=substrapp.storages.minio.MinioStorage("substra-compute-task-logs"),
                upload_to=substrapp.models.asset_failure_report._upload_to,
            ),
        ),
    ]
