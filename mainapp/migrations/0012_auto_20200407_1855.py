# Generated by Django 3.0.5 on 2020-04-07 14:25

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0011_auto_20200407_1849'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='date_requested',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
