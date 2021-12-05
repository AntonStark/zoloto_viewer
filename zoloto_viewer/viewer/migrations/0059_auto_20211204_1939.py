# Generated by Django 3.0.2 on 2021-12-04 16:39

from django.db import migrations


MARKERKIND_UNICODE_SYMBOL = {
    '1': '\uE900',
    '2': '\uE902',
    '3': '\uE903',
    '4': '\uE904',
    'угол': '\uE901',
}


def setup_unicode_symbol(apps, schema_editor):
    MarkerKind = apps.get_model('viewer', 'MarkerKind')
    for mk in MarkerKind.objects.all():
        if mk.name in MARKERKIND_UNICODE_SYMBOL:
            mk.unicode_symbol = MARKERKIND_UNICODE_SYMBOL[mk.name]
            mk.save()


def clear_unicode_symbol(apps, schema_editor):
    MarkerKind = apps.get_model('viewer', 'MarkerKind')
    for mk in MarkerKind.objects.all():
        if mk.name in MARKERKIND_UNICODE_SYMBOL:
            mk.unicode_symbol = ' '
            mk.save()


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0058_markerkind_unicode_symbol'),
    ]

    operations = [
        migrations.RunPython(code=setup_unicode_symbol, reverse_code=clear_unicode_symbol),
    ]