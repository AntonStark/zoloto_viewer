# Generated by Django 3.0.2 on 2021-10-11 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0054_page_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='layergroup',
            name='num',
            field=models.IntegerField(default=0),
        ),
    ]
