# Generated by Django 3.2 on 2021-05-24 14:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('test_app_2', '0006_address_line_split'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='address',
        ),
    ]
