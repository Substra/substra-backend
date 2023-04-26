# Generated by Django 4.1.7 on 2023-04-27 08:42

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("users", "0004_useroidcinfo"),
    ]

    operations = [
        migrations.CreateModel(
            name="BearerToken",
            fields=[
                ("key", models.CharField(max_length=40, primary_key=True, serialize=False, verbose_name="Key")),
                ("created", models.DateTimeField(auto_now_add=True, verbose_name="Created")),
                ("note", models.TextField(null=True)),
                ("expiry", models.DateTimeField(null=True)),
                ("token_id", models.UUIDField(default=uuid.uuid4, editable=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bearer_tokens",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Users",
                    ),
                ),
            ],
            options={
                "verbose_name": "Token",
                "verbose_name_plural": "Tokens",
                "abstract": False,
            },
        ),
    ]
