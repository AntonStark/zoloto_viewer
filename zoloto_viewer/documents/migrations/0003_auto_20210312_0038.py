# Generated by Django 3.0.2 on 2021-03-11 21:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0048_auto_20210223_1712'),
        ('documents', '0002_remove_projectfile_date_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectfile',
            name='layer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='viewer.Layer'),
        ),
        migrations.AlterField(
            model_name='projectfile',
            name='kind',
            field=models.IntegerField(choices=[(1, 'Pdf Exfoliation'), (2, 'Csv Layer Stats'), (3, 'Csv Infoplan'), (4, 'Csv Variables'), (5, 'Csv Pict Codes'), (6, 'Tar Infoplan')]),
        ),
    ]
