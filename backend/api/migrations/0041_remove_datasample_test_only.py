# Generated by Django 4.0.7 on 2023-01-03 15:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0040_alter_computeplan_failed_task_category_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datasample',
            name='test_only',
        ),
    ]
