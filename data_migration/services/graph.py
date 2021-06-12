import os
from importlib import import_module
from types import FunctionType
from typing import Optional, List

from django.apps import apps
from django.db import connections
from django.db.migrations.exceptions import NodeNotFoundError
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

from data_migration.services.node import Node

FunList = List[FunctionType]


class GraphNode:
    """Migration node representation within a graph."""

    def __init__(self, app_name: str, name: str,
                 dependencies: List[str],
                 migration_dependencies: List[str],
                 routines: FunList) -> None:
        self.routines = routines
        self.dependencies = dependencies
        self.migration_dependencies = migration_dependencies
        self.node = self.get_or_prepare_node(app_name, name)
        self.next: Optional[GraphNode] = None
        self.previous: Optional[GraphNode] = None

    @staticmethod
    def get_or_prepare_node(app_name, name) -> Node:
        """
        Return existing Node or object which is not created yet.

        :param app_name: target app
        :param name: name of migration
        :return: node with app_name=app_name, name=name
        """
        node_obj = Node(app_name=app_name, name=name)
        if node_obj.exists():
            node = node_obj.qs.filter(
                app_name=app_name, name=name).first()
            node_obj.pk = node.pk
            node_obj.created_at = node.created_at
        return node_obj

    def set_applied(self):
        """Queries django's migration table to determine whether node was applied before or not"""

        if self.node.is_applied:
            return

        recorder = MigrationRecorder(connections['default'])
        dependency_names = [d.split('.')[-1] for d in self.migration_dependencies]
        django_migrations = recorder.migration_qs.filter(
            app=self.node.app_name, name__in=dependency_names)
        if django_migrations.count() == len(dependency_names):
            self.node.apply()

    def apply(self) -> None:
        """
        Apply node.

        Calling this method will execute the routines within the node.
        If the migration is already applied do nothing.
        """
        if self.node.is_applied:
            return

        if self.prepare_migration_state():
            connection = connections['default']

            # Work out which apps have migrations and which do not
            executor = MigrationExecutor(connection)
            pre_migrate_state = executor._create_project_state(
                with_applied_migrations=True)
            current_state_apps = pre_migrate_state.apps
            with connection.schema_editor(atomic=True) as schema_editor:
                for routine in self.routines:
                    routine(
                        apps=current_state_apps,
                        schema_editor=schema_editor
                    )
        self.node.apply()

    def revert(self) -> None:
        """Reverts an applied migration node."""
        if not self.node.is_applied:
            return

        backup_node = Node(
            name=self.node.name,
            app_name=self.node.app_name
        )
        self.node.qs.get(pk=self.node.pk).delete()
        self.node = backup_node

    def prepare_migration_state(self):
        """Migrates the django migration graph until dependencies are applied"""
        # Get the database we're operating from
        connection = connections['default']

        # Work out which apps have migrations and which do not
        executor = MigrationExecutor(connection)
        pre_migrate_state = executor._create_project_state(
            with_applied_migrations=True)
        migration_graph_in_place = True

        if self.migration_dependencies:
            recorder = MigrationRecorder(connections['default'])
            applied_migrations = recorder.applied_migrations()
            unapplied_dependencies = list()
            for dependency in self.migration_dependencies:
                plan = dependency.split('.')
                plan = tuple([plan[-2], plan[-1]])
                if plan not in applied_migrations:
                    unapplied_dependencies.append(plan)

            if unapplied_dependencies:
                try:
                    plan = executor.migration_plan(unapplied_dependencies)
                    executor.migrate(
                        unapplied_dependencies,
                        plan=plan,
                        state=pre_migrate_state.clone()
                    )
                    migration_graph_in_place = True
                except NodeNotFoundError as ex:
                    for dep in unapplied_dependencies:
                        if not recorder.migration_qs.filter(
                                app=dep[0],
                                name__icontains=dep[1]
                        ).exists():
                            raise ex

            if not migration_graph_in_place:
                migration_graph_in_place = (
                    recorder
                    .migration_qs
                    .filter(app=self.node.app_name)
                    .order_by('-pk').first() in self.migration_dependencies
                )

        return migration_graph_in_place

    def append(self, node) -> None:
        """
        Append a node to the graph by attaching it to the last element.

        :param node: child to append
        """
        if not self.next:
            self.next = node
            node.previous = self
        else:
            self.next.append(node)

    @classmethod
    def from_struct(cls, app_name, obj) -> 'GraphNode':
        """
        Construct node from structured object.

        :param app_name: target application name
        :param obj: structured object to create from
        :return: representation as graph node
        """
        return cls(
            app_name,
            obj.name,
            obj.dependencies,
            obj.migration_dependencies,
            obj.routines
        )

    def __repr__(self) -> str:
        """Node representation."""
        date_str = self.node.created_at.isoformat() \
            if self.node.created_at else ""
        return f'{self.node.name}({date_str})'


class Graph:
    """Directed graph, imitates django's migration graph."""

    class MigrationNotFoundError(Exception):
        """Raised when non existing migration requested."""

        def __init__(self, name):
            super().__init__(f'Data migration "{name}" not found.')

    class EmptyGraphError(Exception):
        """Raised when trying to apply empty graph."""

        def __init__(self):
            super().__init__('Empty graph can\'t be applied.')

    def __init__(self, app_name: str) -> None:
        self.app_name = app_name
        self.base_node: Optional[GraphNode] = None

    def __repr__(self) -> str:
        """Representation of graph."""
        node = self.base_node
        out = str(self.base_node)
        while node.next:
            out += f'->{node.next}'
            node = node.next
        return out

    def push_back(self, child: GraphNode) -> None:
        """
        Append the graph with a new node, or set the first node as base node.

        :param child: node to append
        """
        if not self.base_node:
            self.base_node = child
        else:
            self.base_node.append(child)

    def get_node(self, name: str) -> GraphNode:
        """
        Getter for a node in the graph based on it's name.

        :raises Graph.MigrationNotFoundError: when base not available
        :param name: name of node
        :return: node within the graph
        """
        if name == 'zero':
            return self.base_node

        # no name = latest applied
        if not name:
            try:
                latest_node = Node.Node.objects.filter(
                    app_name=self.app_name).latest()
                name = latest_node.name
            except Node.Node.DoesNotExist:
                return self.base_node

        # search for node in tree with matching name
        node = self.base_node
        if node:
            if node.node.name == name:
                return node
            while node.next:
                if node.node.name == name:
                    return node

                node = node.next

        raise Graph.MigrationNotFoundError(name)

    def apply(self, name: Optional[str] = None,
              fail_silently: bool = False) -> None:
        """
        Apply the migration graph until (and including) given name.

        :raises Graph.EmptyGraphError(): on attempt on empty graph
        :param name: target migration name
        :param fail_silently: raise exception when applying empty graph
        """
        node: GraphNode = self.get_node(name)
        if not node:
            if not fail_silently:
                raise Graph.EmptyGraphError()
            return

        # revert or apply migrations depending on current state
        if (node.next and node.next.node.is_applied) or name == 'zero':
            self.revert_graph(node, name == 'zero')
        else:
            self.forward_graph(node, not bool(name))

    def forward_graph(self, node, complete: bool = True) -> None:
        """
        Apply graph based on nodes recursive.

        :param node: current node to apply
        :param complete: indicator to apply until last node
        """
        latest_node = node
        while (latest_node.previous
               and not latest_node.previous.node.is_applied):
            latest_node = latest_node.previous

        while latest_node:
            latest_node.apply()
            if not complete and latest_node == node:
                break
            latest_node = latest_node.next

    def revert_graph(self, node, complete: bool = False) -> None:
        """
        Reverts graph based on nodes recursive.

        :param node: current node to revert
        :param complete: indicator to revert whole graph
        """
        # walk down the tree
        latest_node = node
        while latest_node.next and latest_node.next.node.is_applied:
            latest_node = latest_node.next

        # revert until given point
        while latest_node:
            latest_node.revert()
            if not complete and latest_node == node:
                break
            latest_node = latest_node.previous

    @staticmethod
    def from_dir(app_name: str) -> 'Graph':
        """
        Generate graph from given app directory.

        :param app_name: name of app to generate graph of
        :return: Fully generated graph for requested app
        """
        app_conf = apps.get_app_config(app_name)
        dir_path = app_conf.path
        dir_path = os.path.join(dir_path, 'data_migrations')
        obj = Graph(app_name)
        files = [f for f in os.listdir(dir_path)
                 if os.path.isfile(os.path.join(dir_path, f))]
        for file in files:
            if file == '__init__.py':
                continue
            file = file.split('.')[0]
            module_name = f'{app_conf.module.__name__}.data_migrations.{file}'
            try:
                node = import_module(module_name).Node
            except AttributeError:
                continue
            obj.push_back(GraphNode.from_struct(app_name, node))
        return obj
