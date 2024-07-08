# Generated by Django 4.2.10 on 2024-07-05 09:13

from django.db import migrations


# Until the previous release, we sent function profiling step in microseconds but saved it as seconds
def update_profiling_step(apps, schema_editor):
    functionprofilingstep_model = apps.get_model("api", "FunctionProfilingStep")

    for row in functionprofilingstep_model.objects.all():
        row.duration /= 1_000_000
        row.save(update_fields=["duration"])


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0060_functionprofilingstep"),
    ]

    operations = [
        migrations.RunPython(update_profiling_step),
    ]
