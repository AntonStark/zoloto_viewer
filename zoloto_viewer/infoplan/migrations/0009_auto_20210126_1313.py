# Generated by Django 3.0.2 on 2021-01-26 10:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('infoplan', '0008_auto_20210126_1211'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='markervariable',
            options={'ordering': ['side', 'key']},
        ),
        migrations.AlterUniqueTogether(
            name='markervariable',
            unique_together={('marker', 'side', 'key')},
        ),
    ]
