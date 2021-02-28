# Generated by Django 3.0.2 on 2021-02-22 17:01

from django.db import migrations, models
import django.db.models.deletion
import zoloto_viewer.documents.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('viewer', '0047_auto_20210222_1655'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, default='', upload_to=zoloto_viewer.documents.models.additional_files_upload_path)),
                ('kind', models.IntegerField(choices=[
                    (1, 'Pdf Exfoliation'),
                    (2, 'Csv Layer Stats'),
                    (3, 'Csv Infoplan'),
                    (4, 'Csv Variables'),
                    (5, 'Csv Pict Codes')
                ])),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='viewer.Project')),
            ],
        ),
    ]