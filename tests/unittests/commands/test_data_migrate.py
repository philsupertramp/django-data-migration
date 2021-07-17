import os
from unittest import TestCase, mock

from data_migration.settings import internal_settings
from tests.unittests.test_app_2.helper import ResetDirectory2Context
from tests.utils import FileTestCase

from django.core.management import call_command

this_dir = os.path.dirname(__file__)


class DataMigrateCommandTestCase(FileTestCase):
    internal_target = os.path.join(this_dir, '../test_app_2/')
    needs_cleanup = False

    def test_explicit_app(self):
        with ResetDirectory2Context():
            call_command('data_migrate', app_labels=['test_app_2'])
            prev_target = self.target
            self.target = os.path.join(prev_target, 'data_migrations/')
            self.assertTrue(self.has_file('0001_0002_split_name.py'))
            self.target = os.path.join(prev_target, 'migrations/')
            self.assertTrue(self.has_file('0001_squashed_0008.py'))

    def test_all_apps(self):
        self.assertIsNotNone(internal_settings.SQUASHABLE_APPS)
        with ResetDirectory2Context():
            call_command('data_migrate', squash_all=True)
            prev_target = self.target
            self.target = os.path.join(prev_target, 'data_migrations/')
            self.assertTrue(self.has_file('0001_0002_split_name.py'))
            self.assertTrue(self.has_file('0002_0006_address_line_split.py'))
            self.target = os.path.join(prev_target, 'migrations/')
            self.assertTrue(self.has_file('0001_squashed_0008.py'))
