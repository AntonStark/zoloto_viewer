# Generated by Django 3.0.2 on 2021-02-22 13:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0046_auto_20210210_1517'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='markerkind',
            options={'ordering': ['id']},
        ),
        migrations.RemoveField(
            model_name='layer',
            name='client_last_modified_date',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='csv_data',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='sync_needed',
        ),
    ]
