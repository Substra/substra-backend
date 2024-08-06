# Generated by Django 4.2.3 on 2024-08-06 16:29

import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_implicitbearertoken_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bearertoken",
            name="expires_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
