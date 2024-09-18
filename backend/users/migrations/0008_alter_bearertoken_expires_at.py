# Generated by Django 4.2.5 on 2024-08-14 15:28

import django.utils.timezone
from django.db import migrations
from django.db import models


def set_default_expires_at(apps, schema_editor):
    BearerToken = apps.get_model("users", "BearerToken")  # noqa
    BearerToken.objects.filter(expires_at__isnull=True).update(expires_at=django.utils.timezone.now())


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_implicitbearertoken_id_and_more"),
    ]

    operations = [
        migrations.RunPython(set_default_expires_at),
        migrations.AlterField(
            model_name="bearertoken",
            name="expires_at",
            field=models.DateTimeField(),
        ),
    ]