# Generated by Django 4.1.7 on 2023-03-17 09:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("users", "0003_setup_role_userchannel"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserOidcInfo",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("openid_issuer", models.TextField()),
                ("openid_subject", models.TextField()),
                ("valid_until", models.DateTimeField()),
                ("refresh_token", models.TextField(blank=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="oidc_info",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
