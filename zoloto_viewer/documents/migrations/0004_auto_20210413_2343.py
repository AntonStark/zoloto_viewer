# Generated by Django 3.0.2 on 2021-04-13 20:43

from django.db import migrations, models
import zoloto_viewer.config.settings.storage_backends
import zoloto_viewer.documents.models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_auto_20210312_0038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectfile',
            name='file',
            field=models.FileField(blank=True, default='',
                                   storage=zoloto_viewer.config.settings.storage_backends.S3MediaStorage(),
                                   upload_to=zoloto_viewer.documents.models.additional_files_upload_path),
        ),
    ]
