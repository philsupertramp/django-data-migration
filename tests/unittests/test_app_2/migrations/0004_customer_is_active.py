# Generated by Django 3.2 on 2021-05-24 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_app_2', '0003_mmodel'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SomeClass',
            new_name='Customer',
        ),
        migrations.AddField(
            model_name='customer',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
