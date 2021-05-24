import os
from unittest import mock

from django.db.migrations.exceptions import NodeNotFoundError
from django.test import TestCase

from data_migration.services.node import Node
from data_migration.services.graph import Graph, GraphNode
from tests.utils import TransactionalTestCase

old_value = 0
new_value = 10
some_value = old_value

this_dir = os.path.dirname(__file__)


def set_some_value(apps, schema_editor) -> None:
    global some_value, new_value
    some_value += new_value


class GraphTestCase(TransactionalTestCase):
    def setUp(self):
        self.reset_global_state()
        Node.flush()

    @staticmethod
    def reset_global_state():
        # reset state
        global some_value
        some_value = old_value

    def test_apply(self):
        g = Graph('test')
        node = GraphNode('test', '0001_init', [], [], [set_some_value])
        g.push_back(node)

        self.assertEqual(some_value, old_value)

        # apply data migration
        g.apply()

        self.assertEqual(some_value, new_value)

        # fail save, reapplying doesn't change the outcome
        g.apply()

        self.assertEqual(some_value, new_value)

    def test_revert(self):
        g = Graph('test')
        g.push_back(GraphNode('test', '0001_init', [], [], []))
        g.push_back(GraphNode('test', '0002_auto', ['0001_init'], [], []))
        g.push_back(GraphNode('test', '0003_auto', ['0002_auto'], [], []))
        g.apply()
        self.assertEqual(Node.get_qs().filter(app_name='test').count(), 3)
        g.apply('zero')
        self.assertEqual(Node.get_qs().filter(app_name='test').count(), 0)
        g.apply('0001_init')
        self.assertEqual(Node.get_qs().filter(app_name='test').count(), 1)
        g.apply('0001_init')
        self.assertEqual(Node.get_qs().filter(app_name='test').count(), 1)
        g.apply('0002_auto')
        self.assertEqual(Node.get_qs().filter(app_name='test').count(), 2)
        g.apply()
        self.assertEqual(Node.get_qs().filter(app_name='test').count(), 3)
        g.apply('zero')
        g.apply('0002_auto')
        self.assertEqual(Node.get_qs().filter(app_name='test').count(), 2)

    def test_wrong_base(self):
        g = Graph('test')
        with self.assertRaises(Graph.MigrationNotFoundError) as ex:
            g.apply('foo123')
            self.assertEqual(str(ex), 'Data migration "foo123" not found.')

        g.push_back(GraphNode('test', 'some_name', [], [], []))

        with self.assertRaises(Graph.MigrationNotFoundError) as ex:
            g.apply('foo123')
            self.assertEqual(str(ex), 'Data migration "foo123" not found.')

    @mock.patch('django.db.migrations.loader.MigrationLoader.migrations_module',
                return_value=('django.contrib.contenttypes.migrations', '__first__'))
    @mock.patch('django.apps.apps.get_app_config')
    def test_from_dir(self, get_app_config_mock, migrations_module_mock):
        get_app_config_mock.return_value = mock.Mock(module=mock.Mock(__name__='tests.unittests.services'), path=this_dir)
        g = Graph.from_dir('tests.unittests.services')
        g.apply()

        self.assertEqual(some_value, new_value)

    def test_unapplied_dependency(self):
        g = Graph('test')
        g.push_back(GraphNode('test', '0001_init', [], ['foobar.0001_init'], []))

        with self.assertRaises(NodeNotFoundError):
            g.apply()

    def test_rebuilding_uses_existing_nodes(self):
        g = Graph('test')
        g.push_back(GraphNode('test', '0001_init', [], [], []))
        g.apply()
        node_id = g.base_node.node.pk

        new_graph_node = GraphNode('test', '0001_init', [], [], [])

        self.assertEqual(new_graph_node.node.pk, node_id)

    def test_fail_silently(self):
        g = Graph('test')
        with self.assertRaises(Graph.EmptyGraphError):
            g.apply()

        g.apply(fail_silently=True)


class GraphNodeTestCase(TransactionalTestCase):
    def test_revert_fails_silently(self):
        node = GraphNode('test', '0001_init', [], [], [])

        node.revert()

        node.apply()
        node.revert()
