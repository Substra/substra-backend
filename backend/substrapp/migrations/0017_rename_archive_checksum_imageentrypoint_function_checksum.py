# Generated by Django 4.1.7 on 2023-10-02 08:44

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("substrapp", "0016_rename_computetaskfailurereport_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="imageentrypoint",
            old_name="function_checksum",
            new_name="archive_checksum",
        ),
    ]
