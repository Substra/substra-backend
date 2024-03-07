from django.db import migrations


def migrate_data(apps, schema_editor):
    status_mapping = {
        "PLAN_STATUS_EMPTY": "PLAN_STATUS_CREATED",
        "PLAN_STATUS_TODO": "PLAN_STATUS_CREATED",
        "PLAN_STATUS_WAITING": "PLAN_STATUS_CREATED",
    }
    model_model = apps.get_model("api", "computeplan")
    for plan_instance in model_model.objects.all():
        new_status = status_mapping.get(plan_instance.status, plan_instance.status)
        plan_instance.category = new_status
        plan_instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0058_alter_compute_task_status"),
    ]

    operations = [
        migrations.RunPython(migrate_data),
    ]
