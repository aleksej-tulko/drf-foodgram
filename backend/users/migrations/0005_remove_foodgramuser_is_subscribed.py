# Generated by Django 3.2.16 on 2025-02-10 22:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_foodgramuser_avatar'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='foodgramuser',
            name='is_subscribed',
        ),
    ]
