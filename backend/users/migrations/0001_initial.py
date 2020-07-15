# Generated by Django 2.1.2 on 2019-08-22 11:22

from django.db import migrations, models
from django.conf import settings
import django.contrib.auth.models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    parent_link=True,
                    to=settings.AUTH_USER_MODEL)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'channel',
                'verbose_name_plural': 'channels',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
