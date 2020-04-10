# Generated by Django 3.0.5 on 2020-04-07 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('os', models.CharField(choices=[('Win', 'Windows'), ('Lin', 'Linux')], max_length=50, verbose_name='')),
                ('app_name', models.CharField(max_length=250, verbose_name='')),
                ('cpu', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='')),
                ('ram', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='')),
                ('disk', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='')),
                ('days', models.IntegerField(default=0, verbose_name='')),
                ('show_cost', models.IntegerField(default=0, verbose_name='')),
                ('description', models.TextField(blank=True, verbose_name='')),
                ('serial_number', models.CharField(editable=False, max_length=16, unique=True, verbose_name='')),
            ],
        ),
    ]