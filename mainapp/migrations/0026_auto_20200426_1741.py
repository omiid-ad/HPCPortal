# Generated by Django 3.0.5 on 2020-04-26 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0025_auto_20200426_1736'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='date_payed',
            field=models.DateTimeField(auto_now_add=True, verbose_name='تاریخ پرداخت'),
        ),
    ]
