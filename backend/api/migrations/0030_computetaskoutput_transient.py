# Generated by Django 4.0.6 on 2022-08-04 09:10

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0029_lastevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="computetaskoutput",
            name="transient",
            field=models.BooleanField(default=False),
        ),
    ]
