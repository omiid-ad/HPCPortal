# Generated by Django 3.0.5 on 2020-04-11 16:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0016_auto_20200411_1638'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='request',
            options={'verbose_name_plural': 'درخواست سرویس'},
        ),
        migrations.CreateModel(
            name='ExtendRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('days', models.IntegerField(default=0, verbose_name='تعداد روزها')),
                ('acceptance_status', models.CharField(choices=[('Pen', 'در انتظار تایید'), ('Acc', 'تایید شده'), ('Rej', 'رد شده')], default='Pen', max_length=200, verbose_name='وضعیت تایید')),
                ('date_expired', models.DateField(editable=False, null=True, verbose_name='تاریخ سررسید بعد از تمدید')),
                ('request', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mainapp.Request', verbose_name='سرویس')),
            ],
            options={
                'verbose_name_plural': 'درخواست های تمدید',
            },
        ),
    ]