# Generated by Django 3.0.5 on 2020-04-20 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0018_auto_20200412_1600'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='user_description',
            field=models.TextField(blank=True, verbose_name='توضیحات کاربر'),
        ),
    ]
