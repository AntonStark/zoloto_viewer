# Generated by Django 3.0.2 on 2020-02-03 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0019_auto_20200202_2347'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='code',
            field=models.CharField(default='a', max_length=10, unique=True),
            preserve_default=False,
        ),
    ]
