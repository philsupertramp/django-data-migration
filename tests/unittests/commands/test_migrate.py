import os.path
from unittest import mock

from data_migration.services.node import Node
from django.core.management import call_command, CommandError
from django.db import transaction
from django.test import TransactionTestCase
from tests.unittests.test_app.helper import ResetDirectoryContext

this_dir = os.path.dirname(__file__)

old_value = 0
new_value = 10
some_value = old_value


def set_some_value(apps) -> None:
    global some_value
    some_value += new_value


class MigrateCommandTestCase(TransactionTestCase):
    def tearDown(self) -> None:
        self.reset_global_state()
        Node.qs.all().delete()

    def run_commit_hooks(self):
        """
        Fake transaction commit to run delayed on_commit functions
        :return:
        """
        for db_name in reversed(self._databases_names()):
            with mock.patch('django.db.backends.base.base.BaseDatabaseWrapper.validate_no_atomic_block',
                            lambda a: False):
                transaction.get_connection(using=db_name).run_and_clear_commit_hooks()

    @staticmethod
    def reset_global_state():
        # reset state
        global some_value
        some_value = old_value

    @mock.patch('django.core.management.commands.migrate.Command.handle')
    def test_extends_default(self, migrate_command):
        migrate_command.return_value = 'Ok.'
        call_command('migrate')
        migrate_command.assert_called_once()
        self.assertEqual(some_value, old_value)

    @mock.patch('django.db.migrations.loader.MigrationLoader.migrations_module',
                return_value=('django.contrib.contenttypes.migrations', '__first__'))
    @mock.patch('django.apps.apps.get_app_config')
    @mock.patch('django.core.management.commands.migrate.Command.handle')
    def test_app_label(self, migrate_command, get_app_config_mock, migration_module_mock):
        global some_value, new_value, old_value

        migrate_command.return_value = 'Ok.'
        get_app_config_mock.return_value = mock.Mock(module=mock.Mock(__name__='tests.unittests.commands.in'), path=os.path.join(this_dir,
                                                                                                                       'in'))
        self.assertEqual(some_value, old_value)

        call_command('migrate', app_label='tests.unittests.commands.in')

        migrate_command.assert_called_once()
        self.assertEqual(some_value, new_value)

    def test_validates_app_label(self):
        with self.assertRaises(CommandError):
            call_command('migrate', app_label='foobar123123')

    @mock.patch('django.db.migrations.loader.MigrationLoader.migrations_module',
                return_value=('tests.unittests.test_app.migrations', '__first__'))
    def test_migrate_with_leaf_migration(self, migration_module_mock):
        global some_value, new_value, old_value
        context = ResetDirectoryContext()
        context.__enter__()

        self.run_commit_hooks()
        call_command('migrate', app_label='test_app', migration_name='zero')

        self.run_commit_hooks()

        self.assertEqual(some_value, old_value)

        call_command('migrate', app_label='test_app')

        self.run_commit_hooks()
        call_command('makemigrations', 'test_app', data_migration=True)

        self.run_commit_hooks()
        call_command('migrate', app_label='test_app')

        self.run_commit_hooks()

        self.assertEqual(some_value, new_value)
        context.__exit__(None, None, None)
