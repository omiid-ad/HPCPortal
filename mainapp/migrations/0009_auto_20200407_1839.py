# Generated by Django 3.0.5 on 2020-04-07 14:09

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0008_auto_20200407_1837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='date_requested',
            field=models.DateField(default=datetime.datetime(2020, 4, 7, 14, 9, 17, 422939, tzinfo=utc)),
        ),
    ]
