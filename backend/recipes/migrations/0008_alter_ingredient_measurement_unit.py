# Generated by Django 3.2.16 on 2025-02-08 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_delete_shortlink'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='measurement_unit',
            field=models.CharField(max_length=10, verbose_name='Единица измерения'),
        ),
    ]
