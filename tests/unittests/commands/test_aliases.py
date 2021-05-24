from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from tests.unittests.test_app.helper import ResetDirectoryContext


class AliasCommandTestCase(TestCase):
    @mock.patch('django.core.management.commands.migrate.Command.handle')
    def test_django_migrate(self, migrate_command):
        migrate_command.return_value = ''
        call_command('django_migrate')
        migrate_command.assert_called_once()

    @mock.patch('django.core.management.commands.makemigrations.Command.handle')
    def test_django_makemigrations(self, migrate_command):
        with ResetDirectoryContext():
            migrate_command.return_value = ''
            call_command('django_makemigrations', ['test_app'])
            migrate_command.assert_called_once()

    @mock.patch('django.core.management.commands.squashmigrations.Command.handle')
    def test_django_squashmigraitons(self, migrate_command):
        migrate_command.return_value = ''
        call_command('django_squashmigrations', 'test_app', '0001_initial')
        migrate_command.assert_called_once()
