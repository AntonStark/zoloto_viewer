# Generated by Django 3.0.2 on 2022-10-29 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0062_auto_20220416_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='level',
            field=models.TextField(null=True),
        ),
    ]
