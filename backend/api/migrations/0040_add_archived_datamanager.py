# Generated by Django 4.0.7 on 2022-09-27 23:14

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0039_computetaskinputasset"),
    ]

    operations = [
        migrations.AddField(
            model_name="datamanager",
            name="archived",
            field=models.BooleanField(default=False),
        ),
    ]
