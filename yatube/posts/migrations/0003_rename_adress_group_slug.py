# Generated by Django 4.1.4 on 2022-12-29 12:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_group_post_group'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='adress',
            new_name='slug',
        ),
    ]
