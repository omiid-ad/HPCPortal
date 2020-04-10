# Generated by Django 3.0.5 on 2020-04-07 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0004_auto_20200407_1756'),
    ]

    operations = [
        migrations.RenameField(
            model_name='request',
            old_name='status',
            new_name='acceptance_status',
        ),
        migrations.AddField(
            model_name='request',
            name='renewal_status',
            field=models.CharField(choices=[('Exp', 'Expired'), ('Ok', 'Okay'), ('Sus', 'Suspended'), ('Can', 'Canceled')], default=('Ok', 'Okay'), max_length=20, verbose_name=''),
        ),
    ]