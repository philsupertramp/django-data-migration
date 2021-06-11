from unittest import TestCase, mock

from data_migration.services.node import Node, AlreadyAppliedError, DatabaseError
from django.db import DatabaseError as DjDatabaseError


class NodeTestCase(TestCase):
    def tearDown(self) -> None:
        Node.Node.objects.all().delete()

    def test_unique_execution(self):
        node = Node(app_name='test', name='0001_initial')
        node.apply()

        with self.assertRaises(AlreadyAppliedError):
            node.apply()

    def test_apply_creates_record(self):
        node = Node(app_name='test', name='0001_initial')
        self.assertIsNone(node.pk)
        node.apply()
        self.assertIsNotNone(node.pk)

    def test_is_applied(self):
        node = Node(app_name='test', name='0001_initial')
        self.assertFalse(node.is_applied)
        node.apply()
        self.assertTrue(node.is_applied)

    @mock.patch('django.db.backends.base.base.BaseDatabaseWrapper.schema_editor')
    def test_ensure_table_side_effect(self, schema_editor_mock):
        schema_editor_mock.side_effect = DjDatabaseError()

        node = Node(app_name='test', name='0001_initial')
        node.has_table = lambda: False

        with self.assertRaises(DatabaseError) as ex:
            node.ensure_table()
            self.assertEqual(str(ex), 'Table "data_migrations" not creatable.')
