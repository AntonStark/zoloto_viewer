# Generated by Django 3.0.2 on 2021-01-25 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infoplan', '0006_auto_20210124_1749'),
    ]

    operations = [
        migrations.AddField(
            model_name='markervariable',
            name='side',
            field=models.IntegerField(default=0),
        ),
    ]