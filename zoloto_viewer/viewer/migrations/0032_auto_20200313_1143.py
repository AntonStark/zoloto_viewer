# Generated by Django 3.0.2 on 2020-03-13 08:43

from django.db import migrations, models
import zoloto_viewer.viewer.models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0031_auto_20200312_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pdfgenerated',
            name='file',
            field=models.FileField(upload_to=zoloto_viewer.viewer.models.pdf_upload_path),
        ),
    ]
