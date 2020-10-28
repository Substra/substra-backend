from django.apps import apps
from django.db import migrations, models

def get_migration(model_name):
    return [
        migrations.AddField(model_name, 'checksum', models.CharField(blank=True, max_length=64)),
        migrations.AlterField(model_name, 'pkhash', models.UUIDField(primary_key=True, editable=False)),
        migrations.RenameField(model_name, 'pkhash', 'key')
    ]


class Migration(migrations.Migration):

    dependencies = [
        ('substrapp', '0003_aggregatealgo'),
    ]

    operations = []

    for model_name in ['Algo', 'DataManager', 'DataSample', 'Model', 'Objective', 'CompositeAlgo', 'AggregateAlgo']:
        migration = get_migration(model_name)
        operations.extend(migration)
