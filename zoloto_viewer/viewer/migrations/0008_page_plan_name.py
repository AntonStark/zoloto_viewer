# Generated by Django 3.0.2 on 2020-01-24 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0007_auto_20200116_1346'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='plan_name',
            field=models.CharField(default=' ', max_length=256),
            preserve_default=False,
        ),
    ]
