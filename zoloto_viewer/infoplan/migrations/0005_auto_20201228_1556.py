# Position related operations from 0004_auto_20201228_1554.py


from django.db import migrations, models


def set_position_from_path_points(apps, schema_editor):
    Marker = apps.get_model('infoplan', 'Marker')

    def multipoint_mid(mp):
        if len(mp) == 3:        # multipoint = [P1, P2, P3]
            return mp[1]        # ignore splines for now
        elif len(mp) == 1:      # multipoint = [P]
            return mp[0]
        else:
            return None

    def center_position(m):
        points = [p for p in map(multipoint_mid, m.points) if p is not None]
        return sum([p[0] for p in points]) / len(points), sum([p[1] for p in points]) / len(points)

    for m in Marker.objects.all():
        m.pos_x, m.pos_y = center_position(m)
        m.save()


class Migration(migrations.Migration):

    dependencies = [
        ('infoplan', '0004_auto_20201228_1554'),
    ]

    operations = [
        migrations.AddField(
            model_name='marker',
            name='pos_x',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='marker',
            name='pos_y',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='marker',
            name='rotation',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(code=set_position_from_path_points, reverse_code=migrations.RunPython.noop),
    ]
