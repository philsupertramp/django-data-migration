import logging
import os
from dataclasses import dataclass
from importlib import import_module
from typing import Optional, List

from django.apps import apps
from django.db import connections
from django.db.migrations.recorder import MigrationRecorder
from django.template import engines
from django.utils import timezone

from data_migration.helper import get_package_version_string
from data_migration.services.graph import GraphNode

current_dir = os.path.dirname(__file__)

log = logging.Logger(__file__)


@dataclass
class Routine:
    method: str
    module: str
    module_name: str
    file_path: str


class DataMigrationGenerator:
    migration_template = os.path.join(
        current_dir,
        'templates/migration.py.txt'
    )

    def __init__(self, app_name, readable_name: Optional[str] = None,
                 set_header: bool = True, empty: bool = False,
                 dry_run: bool = False, routines: List[Routine] = None,
                 migration_dependencies: List[str] = None) -> None:
        self.app_name = app_name
        if isinstance(self.app_name, list):
            self.app_name = self.app_name[0]
            log.warning(
                f'Initialize "{self.__class__.__name__}" using list,'
                f' will generate file for {self.app_name}.'
            )

        self.clean_app_name()
        root_dir = apps.get_app_config(self.app_name).path
        self.file_dir = os.path.join(root_dir, 'data_migrations')
        self.set_header = set_header
        self.empty = empty
        self.dry_run = dry_run
        self.routines: List[Routine] = routines
        if migration_dependencies is None:
            migration_dependencies = []
        self.migration_dependencies: List[str] = migration_dependencies
        self._gen_file(readable_name)

    def clean_app_name(self):
        self.app_name = self.app_name.replace('[\'', '').replace('\']', '')

    def _gen_file(self, readable_name: Optional[str] = None):
        empty_dir = True
        files = []
        if os.path.isdir(self.file_dir):
            files = [
                f for f in os.listdir(self.file_dir)
                if (f != '__init__.py'
                    and os.path.isfile(os.path.join(self.file_dir, f)))
            ]
            empty_dir = len(files) == 0
        elif not self.dry_run:
            # create directory
            os.mkdir(self.file_dir)

            file = open(os.path.join(self.file_dir, '__init__.py'), 'x')
            file.close()

        latest_filename = ''
        if empty_dir:
            # create first migration file
            self.file_name = os.path.join(
                self.file_dir,
                f'0001_{readable_name or "first"}.py'
            )
        else:
            latest_filename = sorted(files)[-1]
            latest_id = int(latest_filename[:4])

            # 0001_first.py or xxxx_auto.py
            name = readable_name or ("auto" if latest_id > 0 else "first")
            file_name = f'{self._get_id(latest_id+1)}_{name}.py'
            self.file_name = os.path.join(self.file_dir, file_name)

        if self.dry_run:
            return

        file = open(self.file_name, 'x')
        file.close()

        if self.empty:
            return

        template_kwargs = {
            'file_name': self.file_name.split('/')[-1].replace('.py', ''),
            'set_header': self.set_header,
            'date': timezone.now().strftime('%Y-%m-%d %H:%M'),
            'package': get_package_version_string(),
            'routines': self.routines,
            'migration_dependencies': self.migration_dependencies
        }

        if not empty_dir and latest_filename:
            template_kwargs.update({
                'dependencies': [latest_filename.replace('.py', '')]
            })

        recorder = MigrationRecorder(connections['default'])
        latest_migration = recorder.migration_qs.filter(
            app=self.app_name
        ).order_by('-applied').first()
        if latest_migration:
            template_kwargs['migration_dependencies'].append(
                f'{self.app_name}.{latest_migration.name}'
            )

        file = open(self.file_name, 'w')
        with open(self.migration_template, 'r') as input_file:
            file.write(self.render_template(
                input_file.read(), **template_kwargs)
            )
        file.close()

    @staticmethod
    def _get_id(index: int) -> str:
        out = str(index)
        while len(out) < 4:
            out = f'0{out}'
        return out

    @staticmethod
    def render_template(content, **context):
        django_engine = engines['django']
        template = django_engine.from_string(content)

        return template.render(context=context)

    def set_applied(self):
        file = self.file_name.split('.')[0].split('/')[-1]
        app_conf = apps.get_app_config(self.app_name)
        module_name = f'{app_conf.module.__name__}.data_migrations.{file}'

        try:
            node = import_module(module_name).Node
        except ModuleNotFoundError:
            return
        node = GraphNode.from_struct(self.app_name, node)
        node.set_applied()
