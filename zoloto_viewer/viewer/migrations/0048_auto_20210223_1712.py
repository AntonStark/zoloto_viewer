# Generated by Django 3.0.2 on 2021-02-23 14:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0047_auto_20210222_1655'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='pdf_started',
        ),
        migrations.DeleteModel(
            name='PdfGenerated',
        ),
    ]
