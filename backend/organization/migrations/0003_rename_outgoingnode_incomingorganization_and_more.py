# Generated by Django 4.0.4 on 2022-06-09 12:27

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organization", "0002_nodeuser"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="OutgoingNode",
            new_name="IncomingOrganization",
        ),
        migrations.RenameModel(
            old_name="NodeUser",
            new_name="OrganizationUser",
        ),
        migrations.RenameModel(
            old_name="IncomingNode",
            new_name="OutgoingOrganization",
        ),
        migrations.RenameField(
            model_name="incomingorganization",
            old_name="node_id",
            new_name="organization_id",
        ),
        migrations.RenameField(
            model_name="outgoingorganization",
            old_name="node_id",
            new_name="organization_id",
        ),
    ]
