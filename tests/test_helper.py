from unittest import TestCase

from data_migration.helper import get_package_version_string


class HelperTestCase(TestCase):
    def test_get_package_version_string(self):
        self.assertEqual(get_package_version_string(), 'data_migration 0.0.1a')
