# Generated by Django 3.0.5 on 2020-04-21 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0019_request_user_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='acceptance_status',
            field=models.CharField(choices=[('Pen', 'در انتظار تایید'), ('Acc', 'تایید شده'), ('Rej', 'رد شده'), ('Exting', 'در انتظار تمدید'), ('Caning', 'در انتظار لغو')], default='Pen', max_length=200, verbose_name='وضعیت تایید'),
        ),
    ]