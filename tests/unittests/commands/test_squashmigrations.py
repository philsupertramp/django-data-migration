import io
import os
from unittest import mock, TestCase

from django.core.management import call_command, CommandError
from tests.unittests.test_app.helper import ResetDirectoryContext
from tests.unittests.test_app_2.helper import ResetDirectory2Context
from tests.utils import FileTestCase
from data_migration.services.squasher import Log

this_dir = os.path.dirname(__file__)


def with_test_output_directory(fun):
    def inner(*args, **kwargs):
        with mock.patch('django.apps.apps.get_app_config') as dir_mock:
            dir_mock.return_value = mock.Mock(
                path=os.path.join(this_dir, 'out')
            )
            return fun(*args, **kwargs)

    return inner


class SquashmigrationsCommandTestCase(FileTestCase):
    target = os.path.join(this_dir, '../test_app_2/data_migrations')
    needs_cleanup = False

    def tearDown(self) -> None:
        if self.needs_cleanup:
            self.clean_directory()
            self.needs_cleanup = False

    @mock.patch('django.core.management.commands.'
                'squashmigrations.Command.handle')
    def test_extends_default(self, migrate_command):
        migrate_command.return_value = 'Ok.'
        with ResetDirectoryContext():
            call_command('squashmigrations', 'test_app', '0001')
            migrate_command.assert_called_once()

    @mock.patch('django.core.management.commands.'
                'squashmigrations.Command.handle')
    def test_app_not_found(self, migrate_command):
        migrate_command.return_value = 'Ok.'
        with self.assertRaises(CommandError):
            call_command('squashmigrations', 'foobar', '0001')

    def test_extended_squashing(self):
        with ResetDirectory2Context():
            call_command(
                'squashmigrations',
                'test_app_2',
                '0001',
                extract_data_migrations=True
            )
            self.assertTrue(self.has_file('0001_0002_split_name.py'))
            self.assertTrue(self.has_file('0002_0006_address_line_split.py'))


class LogTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.output = io.StringIO('')
        self.log = Log(self.output)

    def test_write(self):
        input_string = 'Hello'
        self.log.write(input_string)
        self.assertEqual(self.log.log, input_string + '\n')

    def test_flush(self):
        input_string = 'Hello'
        self.log.write(input_string)
        self.log.flush()
        self.assertEqual(self.log.stdout.getvalue(), input_string + '\n')
        self.assertTrue(self.output.getvalue(), input_string + '\n')
