# Generated by Django 3.0.2 on 2020-01-24 10:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0010_auto_20200124_1257'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='orig_file_name',
        ),
    ]
