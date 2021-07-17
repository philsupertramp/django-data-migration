import os
import shutil
from importlib import import_module
from typing import Optional, List
from unittest import TestCase, mock
from django.test import TransactionTestCase as DjangoTestCase
from django.db import transaction
from data_migration.services.graph import GraphNode
import django


this_dir = os.path.dirname(__file__)
DB_NAME = os.path.join(this_dir, 'db.sqlite3')


class FileTestCase(TestCase):
    internal_target = ''

    def setUp(self) -> None:
        self.target = self.internal_target

    def clean_directory(self):
        shutil.rmtree(os.path.join(self.target))

    def has_file(self, name: str) -> bool:
        try:
            for f in os.listdir(self.target):
                if f == name:
                    return True
        except FileNotFoundError:
            pass
        return False

    def get_file(self, name: str) -> Optional[str]:
        for f in os.listdir(self.target):
            if f == name:
                with open(os.path.join(self.target, f), 'r') as file:
                    content = file.read()
                return content
        return None

    def get_data_migration_node(self, module_path):
        try:
            node = import_module(module_path).Node
            return GraphNode.from_struct(module_path.split('.')[-2], node)
        except AttributeError:
            return None


class TransactionalTestCase(DjangoTestCase):
    def run_commit_hooks(self):
        """
        Fake transaction commit to run delayed on_commit functions
        """
        atomic_module = 'django.db.backends.base.base.BaseDatabaseWrapper' \
                        '.validate_no_atomic_block'
        for db_name in reversed(self._databases_names()):
            with mock.patch(atomic_module, lambda a: False):
                transaction.get_connection(
                    using=db_name
                ).run_and_clear_commit_hooks()


is_django_setup = False


def setup_django():
    global is_django_setup
    try:
        os.remove(DB_NAME)
    except FileNotFoundError:
        pass
    if is_django_setup:
        return

    is_django_setup = True

    from django.conf import settings

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
            'tests.unittests.test_app.apps.TestAppConfig',
            'tests.unittests.test_app_2.apps.TestApp2Config',
        ],
        DATA_MIGRATION={
            'SQUASHABLE_APPS' : [
                'test_app',
                'test_app_2',
            ],
        },
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [os.path.join(this_dir, 'templates')],
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
    migrate()


def migrate():
    from django.core.management import call_command
    from django.db import connections
    call_command('django_migrate')

    with connections['default'].cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.fetchone()


def teardown_django():
    try:
        os.remove(DB_NAME)
    except FileNotFoundError:
        pass
    global is_django_setup
    is_django_setup = False


class ResetDirectoryMixin:
    targets: List[str] = []
    protected_files: List[str] = []
    this_dir: str = ''

    def __enter__(self):
        return True

    def __exit__(self, exc_type, exc_val, exc_tb):
        for target in self.targets:
            dir_path = os.path.join(self.this_dir, target)
            try:
                files = [
                    os.path.join(dir_path, f)
                    for f in os.listdir(dir_path)
                    if f not in self.protected_files
                    and os.path.isfile(os.path.join(dir_path, f))
                ]
            except FileNotFoundError:
                continue
            for file in files:
                os.remove(file)
