# Generated by Django 3.2 on 2021-05-24 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_app_2', '0007_remove_customer_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='is_business',
            field=models.BooleanField(default=False),
        ),
    ]