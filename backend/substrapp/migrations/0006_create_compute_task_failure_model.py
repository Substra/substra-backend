import uuid

import django.core.files.storage
from django.db import migrations
from django.db import models

import substrapp.models.function


class Migration(migrations.Migration):

    dependencies = [
        ("substrapp", "0005_remove_validated_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComputeTaskFailureReport",
            fields=[
                (
                    "compute_task_key",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                (
                    "logs",
                    models.FileField(
                        max_length=36,
                        storage=django.core.files.storage.FileSystemStorage(),
                        upload_to=substrapp.models.compute_task_failure_report._upload_to,
                    ),
                ),
                ("logs_checksum", models.CharField(max_length=64)),
                ("creation_date", models.DateTimeField(auto_now_add=True)),
            ],
        )
    ]
