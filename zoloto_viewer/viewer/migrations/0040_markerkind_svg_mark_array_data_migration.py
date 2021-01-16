# Generated by Django 3.0.2 on 2021-01-10 15:10

from django.db import migrations


MARKERKIND_SVG_FIGURE = {
    '1': '''
<polygon points="1.4475209712982178,0 5.02105712890625,0 3.8068599700927734,2.102991819381714 6.23524284362793,2.102991819381714 5.02105712890625,0 8.59459400177002,0 10.042115211486816,2.919701099395752 0,2.919701099395752"/>
''',
    '2': '''
<polygon points="1.4475209712982178,0 5.02105712890625,0 3.8068599700927734,2.102991819381714 6.23524284362793,2.102991819381714 5.02105712890625,0 8.59459400177002,0 10.042115211486816,2.919701099395752 0,2.919701099395752"/>
''',
    '3': '''
<polygon points="1.4475209712982178,0 5.02105712890625,0 3.8068599700927734,2.102991819381714 6.23524284362793,2.102991819381714 5.02105712890625,0 8.59459400177002,0 10.042115211486816,2.919701099395752 0,2.919701099395752"/>
''',
    '4': '''
<polygon points="1.4475209712982178,0 5.02105712890625,0 3.8068599700927734,2.102991819381714 6.23524284362793,2.102991819381714 5.02105712890625,0 8.59459400177002,0 10.042115211486816,2.919701099395752 0,2.919701099395752"/>
''',
    'угол': '''
<polygon points="1.4475209712982178,0 5.02105712890625,0 3.8068599700927734,2.102991819381714 6.23524284362793,2.102991819381714 5.02105712890625,0 8.59459400177002,0 10.042115211486816,2.919701099395752 0,2.919701099395752"/>
''',
}


def setup_svg_mark_array(apps, schema_editor):
    MarkerKind = apps.get_model('viewer', 'MarkerKind')
    for mk in MarkerKind.objects.all():
        if mk.name in MARKERKIND_SVG_FIGURE:
            mk.svg_figures = MARKERKIND_SVG_FIGURE[mk.name]
            mk.save()


def clear_svg_mark_array(apps, schema_editor):
    MarkerKind = apps.get_model('viewer', 'MarkerKind')
    for mk in MarkerKind.objects.all():
        if mk.name in MARKERKIND_SVG_FIGURE:
            mk.svg_figures = ''
            mk.save()


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0039_markerkind_svg_figures'),
    ]

    operations = [
        migrations.RunPython(code=setup_svg_mark_array, reverse_code=clear_svg_mark_array),
    ]