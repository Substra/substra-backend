# Generated by Django 4.0.3 on 2022-04-19 12:43

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("localrep", "0009_alter_algo_category"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaskDataSamples",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.IntegerField(default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name="computetask",
            name="data_samples",
        ),
        migrations.AddField(
            model_name="computetask",
            name="data_samples",
            field=models.ManyToManyField(
                related_name="compute_tasks", through="localrep.TaskDataSamples", to="localrep.datasample"
            ),
        ),
        migrations.AddField(
            model_name="taskdatasamples",
            name="compute_task",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="compute_task_data_sample",
                to="localrep.computetask",
            ),
        ),
        migrations.AddField(
            model_name="taskdatasamples",
            name="data_sample",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="data_sample_task", to="localrep.datasample"
            ),
        ),
    ]
