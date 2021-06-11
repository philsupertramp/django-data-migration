
from django.db import migrations, models



class Migration(migrations.Migration):

    replaces = [('test_app_2', '0001_initial'), ('test_app_2', '0002_split_name'), ('test_app_2', '0003_mmodel'), ('test_app_2', '0004_customer_is_active'), ('test_app_2', '0005_customer_address'), ('test_app_2', '0006_address_line_split'), ('test_app_2', '0007_remove_customer_address'), ('test_app_2', '0008_customer_is_business')]

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SomeClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=2, null=True)),
                ('first_name', models.CharField(max_length=1, null=True)),
                ('last_name', models.CharField(max_length=1, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='someclass',
            name='name',
        ),
        migrations.CreateModel(
            name='MModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bit', models.BooleanField()),
                ('name', models.CharField(max_length=2, null=True)),
            ],
        ),
        migrations.RenameModel(
            old_name='SomeClass',
            new_name='Customer',
        ),
        migrations.AddField(
            model_name='customer',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='address',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='address_line_1',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='address_line_2',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.RemoveField(
            model_name='customer',
            name='address',
        ),
        migrations.AddField(
            model_name='customer',
            name='is_business',
            field=models.BooleanField(default=False),
        ),
    ]
