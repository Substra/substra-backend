from django.apps import apps
from django.db import migrations, models
from django.db.models import F
import uuid
import re


def copy_pkhash_to_checksum(model_name):
    def _copy_field(apps, schema_editor):
        model = apps.get_model('substrapp', model_name)
        model.objects.all().update(checksum=F('pkhash'))
    return _copy_field


def fix_URIs():
    model = apps.get_model('substrapp', 'Objective')
    model.objects.all().update(description=pkhash_to_uuid(F('description')))
    model.objects.all().update(metrics=pkhash_to_uuid(F('metrics')))


def pkhash_to_uuid(uri):
    # sample input:  objectives/cad5d947bb637e7fffd894c371c237e9c0c18d730dfc2be55ed5dd743431feed/description.md
    # sample output: objectives/cad5d947-bb63-7e7f-ffd8-94c371c237e9/description.md
    return re.sub('/([0-9a-z]{8})([0-9a-z]{4})([0-9a-z]{4})([0-9a-z]{4})([0-9a-z]{12})[0-9a-z]{32}/', r'/\1-\2-\3-\4-\5/', uri)


def get_migration(model_name):
    res =  [
        migrations.AddField(model_name, 'checksum', models.CharField(blank=True, max_length=64)),
        migrations.RunPython(copy_pkhash_to_checksum(model_name)),
        # migrations.RenameField('Model', old_name='pkhash', new_name='key')
    ]
    if model_name in ['Objective']:
        res.append(migrations.AlterField(model_name, 'pkhash', models.CharField(blank=True, max_length=32, primary_key=True, serialize=False)))
        res.append(migrations.AlterField(model_name, 'pkhash', models.UUIDField(primary_key=True, editable=False)))
        res.append(migrations.RunPython(fix_URIs))
    return res


class Migration(migrations.Migration):

    dependencies = [
        ('substrapp', '0003_aggregatealgo'),
    ]

    operations = []

    for model_name in ['Algo', 'DataManager', 'DataSample', 'Model', 'Objective', 'CompositeAlgo', 'AggregateAlgo']:
        migration = get_migration(model_name)
        operations.extend(migration)
