# Generated by Django 3.0.2 on 2020-02-09 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0021_auto_20200209_1848'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='document_offset',
            field=models.PositiveSmallIntegerField(default=None, null=True),
        ),
    ]