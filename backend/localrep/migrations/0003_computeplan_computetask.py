# Generated by Django 4.0.1 on 2022-02-22 12:59

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("localrep", "0002_datamanager_datasample"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComputePlan",
            fields=[
                ("key", models.UUIDField(primary_key=True, serialize=False)),
                ("owner", models.CharField(max_length=100)),
                ("delete_intermediary_models", models.BooleanField(null=True)),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (0, "PLAN_STATUS_UNKNOWN"),
                            (1, "PLAN_STATUS_WAITING"),
                            (2, "PLAN_STATUS_TODO"),
                            (3, "PLAN_STATUS_DOING"),
                            (4, "PLAN_STATUS_DONE"),
                            (5, "PLAN_STATUS_CANCELED"),
                            (6, "PLAN_STATUS_FAILED"),
                        ],
                        default=0,
                    ),
                ),
                ("tag", models.CharField(blank=True, max_length=100)),
                ("creation_date", models.DateTimeField()),
                ("start_date", models.DateTimeField(null=True)),
                ("end_date", models.DateTimeField(null=True)),
                ("metadata", models.JSONField(null=True)),
                ("failed_task_key", models.CharField(max_length=100, null=True)),
                (
                    "failed_task_category",
                    models.IntegerField(
                        choices=[
                            (0, "TASK_UNKNOWN"),
                            (1, "TASK_TRAIN"),
                            (2, "TASK_AGGREGATE"),
                            (3, "TASK_COMPOSITE"),
                            (4, "TASK_TEST"),
                        ],
                        null=True,
                    ),
                ),
                ("channel", models.CharField(max_length=100)),
            ],
            options={
                "ordering": ["creation_date", "key"],
            },
        ),
        migrations.CreateModel(
            name="ComputeTask",
            fields=[
                ("key", models.UUIDField(primary_key=True, serialize=False)),
                (
                    "category",
                    models.IntegerField(
                        choices=[
                            (0, "TASK_UNKNOWN"),
                            (1, "TASK_TRAIN"),
                            (2, "TASK_AGGREGATE"),
                            (3, "TASK_COMPOSITE"),
                            (4, "TASK_TEST"),
                        ]
                    ),
                ),
                ("owner", models.CharField(max_length=100)),
                (
                    "parent_tasks",
                    django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(), null=True, size=None),
                ),
                ("rank", models.IntegerField()),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (0, "STATUS_UNKNOWN"),
                            (1, "STATUS_WAITING"),
                            (2, "STATUS_TODO"),
                            (3, "STATUS_DOING"),
                            (4, "STATUS_DONE"),
                            (5, "STATUS_CANCELED"),
                            (6, "STATUS_FAILED"),
                        ]
                    ),
                ),
                ("worker", models.CharField(max_length=100)),
                ("creation_date", models.DateTimeField()),
                ("start_date", models.DateTimeField(null=True)),
                ("end_date", models.DateTimeField(null=True)),
                (
                    "error_type",
                    models.IntegerField(
                        choices=[
                            (0, "ERROR_TYPE_UNSPECIFIED"),
                            (1, "ERROR_TYPE_BUILD"),
                            (2, "ERROR_TYPE_EXECUTION"),
                            (3, "ERROR_TYPE_INTERNAL"),
                        ],
                        null=True,
                    ),
                ),
                ("tag", models.CharField(blank=True, max_length=100, null=True)),
                ("logs_permission_public", models.BooleanField()),
                (
                    "logs_permission_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), size=100),
                ),
                ("channel", models.CharField(max_length=100)),
                ("metadata", models.JSONField()),
                ("model_permissions_process_public", models.BooleanField(null=True)),
                (
                    "model_permissions_process_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=1024), null=True, size=100
                    ),
                ),
                ("model_permissions_download_public", models.BooleanField(null=True)),
                (
                    "model_permissions_download_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=1024), null=True, size=100
                    ),
                ),
                (
                    "head_permissions_process_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=1024), null=True, size=100
                    ),
                ),
                ("head_permissions_process_public", models.BooleanField(null=True)),
                (
                    "head_permissions_download_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=1024), null=True, size=100
                    ),
                ),
                ("head_permissions_download_public", models.BooleanField(null=True)),
                (
                    "trunk_permissions_process_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=1024), null=True, size=100
                    ),
                ),
                ("trunk_permissions_process_public", models.BooleanField(null=True)),
                (
                    "trunk_permissions_download_authorized_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=1024), null=True, size=100
                    ),
                ),
                ("trunk_permissions_download_public", models.BooleanField(null=True)),
                (
                    "algo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="compute_tasks", to="localrep.algo"
                    ),
                ),
                (
                    "compute_plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="compute_tasks",
                        to="localrep.computeplan",
                    ),
                ),
                (
                    "data_manager",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="compute_tasks",
                        to="localrep.datamanager",
                    ),
                ),
                (
                    "data_samples",
                    django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(), null=True, size=None),
                ),
                ("metrics", models.ManyToManyField(null=True, related_name="compute_tasks", to="localrep.Metric")),
            ],
            options={
                "ordering": ["creation_date", "key"],
            },
        ),
    ]
