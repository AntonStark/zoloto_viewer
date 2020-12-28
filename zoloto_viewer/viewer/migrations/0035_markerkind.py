# Generated by Django 3.0.2 on 2020-12-12 10:36

from django.db import migrations, models


INITIAL_MARKER_KINDS = [
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, 'угол'),
]


def create_marker_kinds(apps, schema_editor):
    MarkerKind = apps.get_model('viewer', 'MarkerKind')
    for id_, name in INITIAL_MARKER_KINDS:
        MarkerKind(id_, name).save()


def sync_sequence():
    return "SELECT SETVAL('public.viewer_markerkind_id_seq', COALESCE(MAX(id), 1) ) FROM public.viewer_markerkind;"


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0034_auto_20200317_1620'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkerKind',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=16)),
            ],
        ),
        migrations.RunPython(create_marker_kinds),
        migrations.RunSQL(sync_sequence()),
    ]