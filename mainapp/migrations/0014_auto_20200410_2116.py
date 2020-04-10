# Generated by Django 3.0.5 on 2020-04-10 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0013_auto_20200409_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='acceptance_status',
            field=models.CharField(choices=[('Pen', 'در انتظار تایید'), ('Acc', 'تایید شده'), ('Rej', 'رد شده')], default=('Pen', 'در انتظار تایید'), max_length=200, verbose_name='وضعیت تایید'),
        ),
        migrations.AlterField(
            model_name='request',
            name='renewal_status',
            field=models.CharField(choices=[('Exp', 'منقضی'), ('Ok', 'نرمال'), ('Sus', 'تعلیق شده'), ('Can', 'لغو شده')], default=('Ok', 'نرمال'), max_length=200, verbose_name='وضعیت سرویس'),
        ),
    ]
