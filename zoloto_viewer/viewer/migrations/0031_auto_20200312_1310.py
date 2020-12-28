# Generated by Django 3.0.2 on 2020-03-12 10:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0030_layer_raw_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='pdf_started',
            field=models.DateTimeField(null=True),
        ),
        migrations.CreateModel(
            name='PdfGenerated',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('mode', models.CharField(choices=[('o', 'original'), ('r', 'reviewed')], max_length=1)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='viewer.Project')),
            ],
        ),
    ]