from django.apps import apps
from django.db import migrations, models
from django.db.models import F
import uuid

def get_migration(model_name):
    res =  [
        migrations.AddField(model_name, 'checksum', models.CharField(blank=True, max_length=64))
    ]
    if model_name in ['Objective', 'DataManager']:
        res.append(migrations.AlterField(model_name, 'pkhash', models.UUIDField(primary_key=True, editable=False)))
    return res


class Migration(migrations.Migration):

    dependencies = [
        ('substrapp', '0003_aggregatealgo'),
    ]

    operations = []

    for model_name in ['Algo', 'DataManager', 'DataSample', 'Model', 'Objective', 'CompositeAlgo', 'AggregateAlgo']:
        migration = get_migration(model_name)
        operations.extend(migration)
