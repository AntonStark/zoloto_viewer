# Generated by Django 3.0.2 on 2020-03-17 13:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0034_auto_20200317_1620'),
        ('infoplan', '0002_auto_20200317_1628'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='marker',
            unique_together={('floor', 'number'), ('layer', 'number')},
        ),
    ]
