# Generated by Django 3.0.2 on 2020-02-02 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0017_auto_20200202_2147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='desc',
            field=models.TextField(blank=True, default=''),
        ),
    ]