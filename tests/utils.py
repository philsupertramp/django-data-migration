import os
from typing import Optional
from unittest import TestCase
import django


this_dir = os.path.dirname(__file__)
DB_NAME = os.path.join(this_dir, 'db.sqlite3')


class FileTestCase(TestCase):
    target = ''

    def clean_directory(self):
        dir_path = os.path.join(self.target, 'out/data_migrations')
        files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f != '.gitkeep']
        for file in files:
            os.remove(file)
        os.removedirs(os.path.join(self.target, 'out/data_migrations'))

    def has_file(self, name: str) -> bool:
        dir_path = os.path.join(self.target, 'out/data_migrations')
        try:
            for f in os.listdir(dir_path):
                if f == name:
                    return True
        except FileNotFoundError:
            pass
        return False

    def get_file(self, name: str) -> Optional[str]:
        dir_path = os.path.join(self.target, 'out/data_migrations')
        for f in os.listdir(dir_path):
            if f == name:
                with open(os.path.join(dir_path, f), 'r') as file:
                    content = file.read()
                return content
        return None


def setup_django():
    try:
        os.remove(DB_NAME)
    except FileNotFoundError:
        pass
    print('SETUP')
    from django.conf import settings
    from django.core.management import call_command

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
            'tests.unittests.test_app.apps.TestAppConfig'
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


def teardown_django():
    try:
        os.remove(DB_NAME)
    except FileNotFoundError:
        pass
