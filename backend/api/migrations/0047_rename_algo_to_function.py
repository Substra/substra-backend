# Generated by Django 4.0.7 on 2023-02-02 17:12

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0046_remove_computeplan_failed_task_category"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Algo",
            new_name="Function",
        ),
        migrations.RenameField(
            model_name="function",
            old_name="algorithm",
            new_name="function_address",
        ),
        migrations.RenameModel(
            old_name="AlgoInput",
            new_name="FunctionInput",
        ),
        migrations.RenameModel(
            old_name="AlgoOutput",
            new_name="FunctionOutput",
        ),
        migrations.RenameField(
            model_name="functionoutput",
            old_name="algo",
            new_name="function",
        ),
        migrations.RenameField(
            model_name="functioninput",
            old_name="algo",
            new_name="function",
        ),
        migrations.RenameField(
            model_name="computetask",
            old_name="algo",
            new_name="function",
        ),
    ]
