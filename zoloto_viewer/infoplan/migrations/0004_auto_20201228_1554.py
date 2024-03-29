# Generated by Django 3.0.2 on 2020-12-28 12:54


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0037_auto_20201212_1655'),
        ('infoplan', '0003_auto_20200317_1643'),
    ]

    operations = [
        migrations.AddField(
            model_name='marker',
            name='ordinal',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='marker',
            unique_together={('floor', 'layer', 'ordinal')},
        ),
        migrations.RemoveField(
            model_name='marker',
            name='number',
        ),
    ]
