# Generated by Django 4.0.7 on 2022-09-27 23:14

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0037_remove_model_category"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="algo",
            name="category",
        ),
    ]
