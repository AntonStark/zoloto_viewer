# Generated by Django 3.0.2 on 2020-12-12 13:27

from django.db import migrations, models


INITIAL_COLORS = [
    # 1 black
    ('#000000', 'rgb(0,0,0)'),
    # 7 normal colors
    ('#FF0000', 'rgb(255,0,0)'),
    ('#FF6600', 'rgb(255,102,0)'),
    ('#FFFF33', 'rgb(255,255,51)'),
    ('#00FF00', 'rgb(0,255,0)'),
    ('#33FFFF', 'rgb(51,255,255)'),
    ('#0000FF', 'rgb(0,0,255)'),
    ('#FF00FF', 'rgb(255,0,255)'),
    # 6 dark (no sky blue)
    ('#CC0000', 'rgb(204,0,0)'),
    ('#CC6600', 'rgb(204,102,0)'),
    ('#FFCC33', 'rgb(255,204,51)'),
    ('#00CC33', 'rgb(0,204,51)'),
    ('#000066', 'rgb(0,0,102)'),
    ('#6600CC', 'rgb(102,0,204)'),
    # 6 light (no sky blue)
    ('#FF6699', 'rgb(255,102,153)'),
    ('#FF9933', 'rgb(255,153,51)'),
    ('#FFFF99', 'rgb(255,255,153)'),
    ('#66FF99', 'rgb(102,255,153)'),
    ('#0099FF', 'rgb(0,153,255)'),
    ('#9900FF', 'rgb(153,0,255)'),
    # 2 dark-dark for red and green
    ('#990000', 'rgb(153,0,0)'),
    ('#006600', 'rgb(0,102,0)'),
]   # 22 total


def create_colors(apps, schema_editor):
    Color = apps.get_model('viewer', 'Color')
    for hex_, rgb in INITIAL_COLORS:
        Color(hex_code=hex_, rgb_code=rgb).save()


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0035_markerkind'),
    ]

    operations = [
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hex_code', models.CharField(default='#000000', max_length=7)),
                ('rgb_code', models.CharField(default='rgb(0,0,0)', max_length=16)),
            ],
        ),
        migrations.RunPython(create_colors),
    ]
