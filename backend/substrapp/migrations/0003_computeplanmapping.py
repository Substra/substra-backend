# Generated by Django 2.2.24 on 2021-08-17 22:32

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('substrapp', '0002_auto_20210816_2217'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComputePlanWorkerMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('compute_plan_key', models.UUIDField()),
                ('worker_index', models.IntegerField()),
                ('release_date', models.DateTimeField(null=True, default=None)),
            ],
        ),
        migrations.AddConstraint(
            model_name='ComputePlanWorkerMapping',
            constraint=models.UniqueConstraint(condition=models.Q(release_date=None), fields=('compute_plan_key',), name='unique_empty_release_date_for_each_compute_plan'),
        ),
    ]
