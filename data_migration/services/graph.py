import os
from importlib import import_module
from types import FunctionType
from typing import Optional, List

from django.apps import apps
from django.db import connections
from django.db.migrations.exceptions import NodeNotFoundError
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

from data_migration.services.node import  Node

FunList = List[FunctionType]


class GraphNode:
    def __init__(self, app_name: str, name: str, dependencies: List[str], migration_dependencies: List[str], routines: FunList) -> None:
        self.routines = routines
        self.dependencies = dependencies
        self.migration_dependencies = migration_dependencies
        self.node = self.get_or_prepare_node(app_name, name)
        self.next: Optional[GraphNode] = None
        self.previous: Optional[GraphNode] = None

    @staticmethod
    def get_or_prepare_node(app_name, name):
        node_obj = Node(app_name=app_name, name=name)
        if node_obj.exists():
            node = node_obj.qs.filter(app_name=app_name, name=name).first()
            node_obj.pk = node.pk
            node_obj.created_at = node.created_at
        return node_obj

    def apply(self):
        if self.node.is_applied:
            return

        # Get the database we're operating from
        connection = connections['default']

        # Work out which apps have migrations and which do not
        executor = MigrationExecutor(connection)
        pre_migrate_state = executor._create_project_state(with_applied_migrations=True)
        current_state_apps = pre_migrate_state.apps
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
                    post_migrate_state = executor.migrate(unapplied_dependencies, plan=plan, state=pre_migrate_state.clone())
                    migration_graph_in_place = True
                except NodeNotFoundError as ex:
                    for dep in unapplied_dependencies:
                        if not recorder.migration_qs.filter(app=dep[0], name__icontains=dep[1]).exists():
                            raise ex
                else:
                    # post_migrate signals have access to all models. Ensure that all models
                    # are reloaded in case any are delayed.
                    post_migrate_state.clear_delayed_apps_cache()
                    current_state_apps = post_migrate_state.apps

            if not migration_graph_in_place:
                migration_graph_in_place = (recorder
                                            .migration_qs
                                            .filter(app=self.node.app_name)
                                            .order_by('-pk').first() in self.migration_dependencies)

        if migration_graph_in_place:
            with connections['default'].schema_editor(atomic=True) as schema_editor:
                for routine in self.routines:
                    routine(apps=current_state_apps, schema_editor=schema_editor)
        self.node.apply()

    def revert(self):
        if not self.node.is_applied:
            return

        backup_node = Node(name=self.node.name, app_name=self.node.app_name)
        self.node.qs.get(pk=self.node.pk).delete()
        self.node = backup_node

    def append(self, node):
        if not self.next:
            self.next = node
            node.previous = self
        else:
            self.next.append(node)

    @classmethod
    def from_struct(cls, app_name, obj):
        return cls(app_name, obj.name, obj.dependencies, obj.migration_dependencies, obj.routines)

    def __repr__(self) -> str:
        return f'{self.node.name}({self.node.created_at.isoformat() if self.node.created_at else ""})'


class Graph:
    """
    directed graph, incorporates django's migration graph
    """
    class MigrationNotFoundError(Exception):
        def __init__(self, name):
            super().__init__(f'Data migration "{name}" not found.')

    class EmptyGraphError(Exception):
        def __init__(self):
            super().__init__(f'Empty graph can\'t be applied.')

    def __init__(self, app_name: str) -> None:
        self.app_name = app_name
        self.base_node: Optional[GraphNode] = None

    def __repr__(self) -> str:
        """
        string representation of graph
        :return:
        """
        node = self.base_node
        out = str(self.base_node)
        while node.next:
            out += f'->{node.next}'
            node = node.next
        return out

    def push_back(self, child: GraphNode) -> None:
        if not self.base_node:
            self.base_node = child
        else:
            self.base_node.append(child)

    def get_base(self, name) -> GraphNode:
        if name == 'zero':
            return self.base_node

        # no name = latest applied
        if not name:
            try:
                latest_node = Node.Node.objects.filter(app_name=self.app_name).latest()
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

    def apply(self, name: Optional[str] = None, fail_silently: bool = False) -> None:
        node: GraphNode = self.get_base(name)
        if not node:
            if not fail_silently:
                raise Graph.EmptyGraphError()
            return

        # revert or apply migrations depending on current state
        if (node.next and node.next.node.is_applied) or name == 'zero':
            self.revert_tree(node, name == 'zero')
        else:
            self.forward_tree(node, not bool(name))

    def forward_tree(self, node, complete: bool = True):
        latest_node = node
        while latest_node.previous and not latest_node.previous.node.is_applied:
            latest_node = latest_node.previous

        while latest_node:
            latest_node.apply()
            if not complete and latest_node == node:
                break
            latest_node = latest_node.next

    def revert_tree(self, node, complete: bool = False):
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
        app_conf = apps.get_app_config(app_name)
        dir_path = app_conf.path
        dir_path = os.path.join(dir_path, 'data_migrations')
        obj = Graph(app_name)
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
        for file in files:
            if file == '__init__.py':
                continue
            file = file.split('.')[0]
            try:
                node = import_module(f'{app_conf.module.__name__}.data_migrations.{file}').Node
            except AttributeError:
                continue
            obj.push_back(GraphNode.from_struct(app_name, node))
        return obj
