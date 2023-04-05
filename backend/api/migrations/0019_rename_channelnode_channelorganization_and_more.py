# Generated by Django 4.0.4 on 2022-06-09 12:27

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0018_alter_algo_category"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ChannelNode",
            new_name="ChannelOrganization",
        ),
        migrations.AlterModelOptions(
            name="channelorganization",
            options={"ordering": ["organization_id"]},
        ),
        migrations.RemoveConstraint(
            model_name="channelorganization",
            name="unique_id_for_channel",
        ),
        migrations.RenameField(
            model_name="channelorganization",
            old_name="node_id",
            new_name="organization_id",
        ),
        migrations.AddConstraint(
            model_name="channelorganization",
            constraint=models.UniqueConstraint(fields=("organization_id", "channel"), name="unique_id_for_channel"),
        ),
    ]
