# Generated by Django 4.0.6 on 2022-08-17 08:53

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0031_taskprofiling_profilingstep"),
    ]

    operations = [
        migrations.AlterField(
            model_name="computeplan",
            name="status",
            field=models.CharField(
                choices=[
                    ("PLAN_STATUS_WAITING", "Plan Status Waiting"),
                    ("PLAN_STATUS_TODO", "Plan Status Todo"),
                    ("PLAN_STATUS_DOING", "Plan Status Doing"),
                    ("PLAN_STATUS_DONE", "Plan Status Done"),
                    ("PLAN_STATUS_CANCELED", "Plan Status Canceled"),
                    ("PLAN_STATUS_FAILED", "Plan Status Failed"),
                    ("PLAN_STATUS_EMPTY", "Plan Status Empty"),
                ],
                default="PLAN_STATUS_EMPTY",
                max_length=64,
            ),
        ),
    ]
