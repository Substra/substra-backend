# Generated by Django 4.2.9 on 2024-02-19 10:27

from django.db import migrations
from django.db import models


def migrate_data(apps, schema_editor):
    status_mapping = {
        "PLAN_STATUS_EMPTY": "PLAN_STATUS_CREATED",
        "PLAN_STATUS_TODO": "PLAN_STATUS_CREATED",
        "PLAN_STATUS_WAITING": "PLAN_STATUS_CREATED",
    }
    model_model = apps.get_model("api", "computeplan")
    for plan_instance in model_model.objects.all():
        new_status = status_mapping.get(plan_instance.status, plan_instance.status)
        plan_instance.status = new_status
        plan_instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0056_alter_computetask_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="computeplan",
            name="status",
            field=models.CharField(
                choices=[
                    ("PLAN_STATUS_CREATED", "Plan Status Created"),
                    ("PLAN_STATUS_DOING", "Plan Status Doing"),
                    ("PLAN_STATUS_DONE", "Plan Status Done"),
                    ("PLAN_STATUS_CANCELED", "Plan Status Canceled"),
                    ("PLAN_STATUS_FAILED", "Plan Status Failed"),
                ],
                default="PLAN_STATUS_CREATED",
                max_length=64,
            ),
        ),
        migrations.RunPython(migrate_data),
    ]
