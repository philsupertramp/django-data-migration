import os.path
from unittest import mock

from data_migration.services.node import Node
from django.core.management import call_command, CommandError
from tests.unittests.test_app.helper import ResetDirectoryContext
from tests.utils import TransactionalTestCase

this_dir = os.path.dirname(__file__)

old_value = 0
new_value = 10
some_other_value = old_value


def set_some_value(apps, schema_editor) -> None:
    global some_other_value
    some_other_value += new_value


class MigrateCommandTestCase(TransactionalTestCase):
    def tearDown(self) -> None:
        self.reset_global_state()
        Node.flush()

    @staticmethod
    def reset_global_state():
        # reset state
        global some_other_value
        some_other_value = old_value

    @staticmethod
    def get_val():
        global some_other_value
        return some_other_value

    @mock.patch('django.core.management.commands.migrate.Command.handle')
    def test_extends_default(self, migrate_command):
        migrate_command.return_value = 'Ok.'
        call_command('migrate')
        migrate_command.assert_called_once()
        self.assertEqual(some_other_value, old_value)

    @mock.patch('django.core.management.commands.migrate.Command.handle')
    def test_only_data(self, migrate_command):
        migrate_command.return_value = 'Ok.'
        call_command('migrate', data_migration=True)
        migrate_command.assert_not_called()
        self.assertEqual(some_other_value, old_value)

    @mock.patch('django.db.migrations.loader.MigrationLoader.migrations_module',
                return_value=('django.contrib.contenttypes.migrations', '__first__'))
    @mock.patch('django.apps.apps.get_app_config')
    @mock.patch('django.core.management.commands.migrate.Command.handle')
    def test_app_label(self, migrate_command, get_app_config_mock, migration_module_mock):
        global some_other_value, new_value, old_value

        migrate_command.return_value = 'Ok.'
        get_app_config_mock.return_value = mock.Mock(module=mock.Mock(__name__='tests.unittests.commands.in'), path=os.path.join(this_dir,
                                                                                                                       'in'))
        self.assertEqual(some_other_value, old_value)

        call_command('migrate', app_label='tests.unittests.commands.in')

        migrate_command.assert_called_once()
        self.assertEqual(some_other_value, new_value)

    def test_validates_app_label(self):
        with self.assertRaises(CommandError):
            call_command('migrate', app_label='foobar123123')


class ExtendedMigrateCommandTestCase(TransactionalTestCase):
    def tearDown(self) -> None:
        self.reset_global_state()
        Node.flush()

    @staticmethod
    def reset_global_state():
        # reset state
        global some_other_value
        some_other_value = old_value

    @staticmethod
    def get_val():
        global some_other_value
        return some_other_value

    @mock.patch('django.db.migrations.loader.MigrationLoader.migrations_module',
                return_value=('tests.unittests.test_app.migrations', '__first__'))
    def test_migrate_with_leaf_migration(self, migration_module_mock):
        with ResetDirectoryContext():
            call_command('migrate', app_label='test_app', migration_name='zero', data_migration=True)

            self.assertEqual(self.get_val(), old_value)

            call_command('makemigrations', ['test_app'], data_migration=True)
            call_command('migrate', app_label='test_app')

            self.assertEqual(self.get_val(), new_value)
