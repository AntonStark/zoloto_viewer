# Generated by Django 3.0.2 on 2020-01-09 09:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0005_auto_20200109_1224'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='marker',
            unique_together={('floor', 'number')},
        ),
    ]
