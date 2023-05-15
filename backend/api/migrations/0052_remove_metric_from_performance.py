# Generated by Django 4.1.7 on 2023-05-09 15:22

from django.db import migrations


def migrate_performances(apps, schema_editor):
    performance_model = apps.get_model("api", "performance")

    for performance_instance in performance_model.objects.all():
        compute_task_output = performance_instance.compute_task_output.get()
        compute_task_output_asset = compute_task_output.assets.get()

        compute_task_output.identifier = performance_instance.metric.name

        compute_task_key, _, identifier = compute_task_output_asset.asset_key.split("|")
        compute_task_output_asset.asset_key = compute_task_key + "|" + identifier

        compute_task_output_asset.save()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0051_alter_performance_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="performance",
            unique_together=set(),
        ),
        migrations.RunPython(migrate_performances),
        migrations.RemoveField(
            model_name="performance",
            name="metric",
        ),
    ]
