# Generated by Django 3.0.5 on 2020-04-07 13:26

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0003_request_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='date_requested',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='request',
            name='status',
            field=models.CharField(choices=[('Pen', 'Pending'), ('Acc', 'Accepted'), ('Rej', 'Rejected')], default=('Pen', 'Pending'), max_length=20, verbose_name=''),
        ),
    ]
