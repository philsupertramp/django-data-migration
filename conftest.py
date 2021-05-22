import os.path

import django
from django.conf import settings
from django.core.management import call_command

this_dir = os.path.dirname(__file__)
DB_NAME = os.path.join(this_dir, 'db.sqlite3')


def pytest_sessionstart(*args, **kwargs):
    try:
        os.remove(DB_NAME)
    except FileNotFoundError:
        pass

    settings.configure(
        SECRET_KEY='xxx',
        DATABASES={'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DB_NAME,
        }},
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'data_migration',
            'tests.test_app.apps.TestAppConfig'
        ],
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [os.path.join(this_dir, 'templates')]
                ,
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ],
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    )
    django.setup()
    call_command('django_migrate')

    from django.db import connections
    with connections['default'].cursor() as cursor:
        cursor.execute("PRAGMA foreign_key_checks = OFF;")


def pytest_sessionfinish(*args, **kwargs):
    os.remove(DB_NAME)
