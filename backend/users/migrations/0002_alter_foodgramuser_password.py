# Generated by Django 3.2.16 on 2025-01-21 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foodgramuser',
            name='password',
            field=models.CharField(max_length=200, verbose_name='Пароль'),
        ),
    ]
