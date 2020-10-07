from django.apps import apps
from django.db import migrations, models
from django.db.models import F


def copy_pkhash_to_checksum(model_name):
    def _copy_field(apps, schema_editor):
        model = apps.get_model('substrapp', model_name)
        model.objects.all().update(checksum=F('pkhash'))
    return _copy_field


def get_migration(model_name):
    return [
        migrations.AddField(model_name, 'checksum', models.CharField(blank=True, max_length=64)),
        migrations.RunPython(copy_pkhash_to_checksum(model_name)),
        # migrations.RenameField('Model', old_name='pkhash', new_name='key')
    ]


class Migration(migrations.Migration):

    dependencies = [
        ('substrapp', '0003_aggregatealgo'),
    ]

    operations = []

    for model_name in ['Algo', 'DataManager', 'DataSample', 'Model', 'Objective', 'CompositeAlgo', 'AggregateAlgo']:
        migration = get_migration(model_name)
        operations.extend(migration)
