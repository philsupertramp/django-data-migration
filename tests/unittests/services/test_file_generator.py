import os
from unittest import mock

from django.db import connections
from django.db.migrations.recorder import MigrationRecorder

from data_migration.services.file_generator import DataMigrationGenerator

from tests.utils import FileTestCase


this_dir = os.path.dirname(__file__)


def with_test_output_directory(fun):
    def inner(*args, **kwargs):
        with mock.patch('django.apps.apps.get_app_config') as dir_mock:
            dir_mock.return_value = mock.Mock(
                path=os.path.join(this_dir, 'out')
            )
            return fun(*args, **kwargs)

    return inner


class DataMigrationGeneratorTestCase(FileTestCase):
    internal_target = os.path.join(this_dir, 'out/data_migrations')

    def tearDown(self) -> None:
        self.clean_directory()

    @with_test_output_directory
    def test_generates_file(self):
        DataMigrationGenerator('test')
        self.assertTrue(self.has_file('0001_first.py'))

    @with_test_output_directory
    @mock.patch('data_migration.services.file_generator.'
                'DataMigrationGenerator.render_template')
    def test_empty(self, render_mock):
        DataMigrationGenerator('test', empty=True)
        render_mock.assert_not_called()

    @with_test_output_directory
    @mock.patch('data_migration.services.file_generator.'
                'DataMigrationGenerator.render_template')
    def test_without_header(self, render_mock):
        render_mock.return_value = ''
        DataMigrationGenerator('test', set_header=False)
        render_mock.assert_called_once()
        render_mock.called_with(file_name='0001_first', set_header=False)

    @with_test_output_directory
    def test_create_with_existing_directory(self):
        dir_path = os.path.join(this_dir, 'out/data_migrations')
        os.mkdir(dir_path)

        file = open(os.path.join(dir_path, '__init__.py'), 'x')
        file.close()

        DataMigrationGenerator('test', 'bigStart')
        self.assertTrue(self.has_file('0001_bigStart.py'))

        DataMigrationGenerator('test', 'auto')
        self.assertTrue(self.has_file('0002_auto.py'))

        DataMigrationGenerator('test')
        self.assertTrue(self.has_file('0003_auto.py'))

    @with_test_output_directory
    def test_sets_latest_migration_dependency(self):
        migration_name = '0001_init'
        recorder = MigrationRecorder(connections['default'])
        recorder.Migration(app='test', name=migration_name).save()
        DataMigrationGenerator('test')
        file_content = self.get_file('0001_first.py')

        self.assertIn(f'test.{migration_name}', file_content)

    @with_test_output_directory
    def test_sets_latest_data_migration_dependency(self):
        DataMigrationGenerator('test')
        DataMigrationGenerator('test')
        file_content = self.get_file('0002_auto.py')

        self.assertIn('0001_first', file_content)

    @with_test_output_directory
    def test_init_with_app_name_list(self):
        DataMigrationGenerator(['test'])
        self.assertTrue(self.has_file('0001_first.py'))

    @with_test_output_directory
    def test_with_dependencies(self):
        migration_dependencies = ['test.0001_init']
        DataMigrationGenerator(['test'], readable_name='test',
                               migration_dependencies=migration_dependencies)
        self.assertTrue(self.has_file('0001_test.py'))

        node = self.get_data_migration_node(
            'tests.unittests.services.out.data_migrations.0001_test'
        )

        self.assertIsNotNone(node)
        self.assertTrue(hasattr(node, 'migration_dependencies'))
        self.assertEqual(
            set(node.migration_dependencies),
            set(migration_dependencies)
        )
        self.assertTrue(hasattr(node, 'dependencies'))

    @mock.patch('django.apps.apps.get_app_config')
    @mock.patch('importlib.import_module')
    def test_set_applied_fails_gracefully(self, import_mock, app_config_mock):
        app_config_mock.return_value = mock.Mock(
            path=os.path.join(this_dir, 'out'), module=mock.Mock(__name__='foo')
        )
        import_mock.side_effect = ModuleNotFoundError()
        # works without issue
        DataMigrationGenerator(['foo']).set_applied()
