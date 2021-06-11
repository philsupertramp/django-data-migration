import os
from unittest import mock

from django.core.management import call_command
from tests.unittests.test_app.helper import ResetDirectoryContext
from tests.utils import FileTestCase

this_dir = os.path.dirname(__file__)


def with_test_output_directory(fun):
    def inner(*args, **kwargs):
        with mock.patch('django.apps.apps.get_app_config') as dir_mock:
            dir_mock.return_value = mock.Mock(path=os.path.join(this_dir, 'out'))
            return fun(*args, **kwargs)

    return inner


class MakemigrationsCommandTestCase(FileTestCase):
    target = os.path.join(this_dir, 'out/data_migrations')
    needs_cleanup = False

    def tearDown(self) -> None:
        if self.needs_cleanup:
            self.clean_directory()
            self.needs_cleanup = False

    @mock.patch('django.core.management.commands.makemigrations.Command.handle')
    def test_extends_default(self, migrate_command):
        migrate_command.return_value = 'Ok.'
        with ResetDirectoryContext():
            call_command('makemigrations', 'test_app')
            migrate_command.assert_called_once()

    @with_test_output_directory
    @mock.patch('django.core.management.commands.makemigrations.Command.handle')
    def test_create_data_migration_file(self, migrate_command):
        with ResetDirectoryContext():
            call_command('makemigrations', ['test_app'], data_migration=True)
            migrate_command.assert_not_called()
            self.assertTrue(self.has_file('0001_first.py'))
            self.needs_cleanup = True

    @with_test_output_directory
    @mock.patch('django.core.management.commands.makemigrations.Command.handle')
    def test_dry_run_does_not_create_files(self, migrate_command):
        with ResetDirectoryContext():
            call_command('makemigrations', ['test_app'], data_migration=True, dry_run=True)
            migrate_command.assert_not_called()
            self.assertFalse(self.has_file('0001_first.py'))
