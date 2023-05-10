# Generated by Django 4.1.7 on 2023-04-26 15:50

import django.db.models.deletion
from django.db import migrations
from django.db import models


def migrate_performances(apps, schema_editor):
    performance_model = apps.get_model("api", "performance")

    for performance_instance in performance_model.objects.all():
        performance_instance.compute_task_output = performance_instance.compute_task.outputs.all()[0]
        performance_instance.compute_task_output.identifier = performance_instance.metric.name
        performance_instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0050_alter_datamanager_channel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="computetaskoutputasset",
            name="asset_key",
            field=models.CharField(max_length=150),
        ),
        migrations.AlterUniqueTogether(
            name="performance",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="performance",
            name="compute_task_output",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="performances",
                to="api.computetaskoutput",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(migrate_performances),
        migrations.AlterField(
            model_name="performance",
            name="compute_task_output",
            field=models.ForeignKey(
                null=False,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="performances",
                to="api.computetaskoutput",
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="performance",
            unique_together={("compute_task_output", "metric")},
        ),
        migrations.RemoveField(
            model_name="performance",
            name="compute_task",
        ),
    ]