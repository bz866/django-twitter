# Generated by Django 3.1.3 on 2021-05-10 01:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tweets', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tweet',
            options={'ordering': [['user', '-created_at']]},
        ),
        migrations.AlterIndexTogether(
            name='tweet',
            index_together=set(),
        ),
    ]
