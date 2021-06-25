import os
import sys
from typing import List, Dict

from data_migration.services.file_generator import DataMigrationGenerator,\
    Routine
from django.apps import apps
from django.core.management import call_command
from django.db.migrations import Migration
from django.db.migrations.executor import MigrationExecutor
from django.db import connection


MigrationPlan = List[Migration]
MigrationGraph = Dict[str, List[Migration]]


class Log:
    def __init__(self, out=sys.stdout):
        self.stdout = out
        self.log = ''

    def write(self, message):
        self.log += f'{message}\n'

    def flush(self):
        self.stdout.write(self.log)
        self.log = ''


log = Log()
sys.stdout = log


class MigrationFile:
    def __init__(self, fn: str, replacement_string: str, pos: int):
        self.file_name: str = fn
        self.replacement_string: str = replacement_string
        self.position: int = pos


class MigrationManager:
    def __init__(self, app_name: str, starting_point: str,
                 end_point: str, dry_run: bool = False):
        self.app_name: str = app_name
        self.start: str = starting_point
        self.end: str = end_point
        self.requires_action: bool = False
        self.migration_files_to_touch: List[MigrationFile] = []
        self.file_name = None
        self.new_file_name = None
        self.temp_file_name = None
        self.temp_directory = None
        self.dry_run = dry_run

    def load(self):
        self.file_name = self.gen_file_name()
        self.new_file_name = self.gen_new_file_name()
        self.temp_file_name = self.gen_temp_file_name()
        self.temp_directory = '/'.join(self.file_name.split('/')[:-1] + ['temp'])

    def __repr__(self):
        return self.file_name

    @property
    def app_path(self) -> str:
        return apps.get_app_config(self.app_name).path

    def gen_file_name(self) -> str:
        return f'{self.app_path}/migrations/{self.start}' \
               f'_squashed_{self.end}.py'

    def gen_temp_file_name(self) -> str:
        return f'{self.app_path}/migrations/temp/{self.start}' \
               f'_squashed_{self.end}.py'

    def gen_new_file_name(self) -> str:
        return f'{self.app_path}/migrations/' \
               f'{self.start.split("_")[0]}' \
               f'_squashed_{self.end.split("_")[0]}.py'

    def _parse_generated_file(self):
        parse_start = False
        with open(self.temp_file_name, 'r') as file:
            char_count = 0
            line = "–"
            replacement_string = '# RunPython operations to refer ' \
                                 'to the local versions:'
            while line != "":
                line = file.readline()
                if replacement_string in line:
                    parse_start = True
                    self.requires_action = True
                elif parse_start and '#' in line:
                    partial_path = line.replace('# ', '').replace('\n', '')
                    migration_path = f'{partial_path.replace(".", "/")}.py'
                    self.migration_files_to_touch.append(
                        MigrationFile(
                            migration_path,
                            partial_path,
                            char_count
                        )
                    )

                char_count += len(line)

    def run(self):
        self.load()

        if self.dry_run:
            log.write(f'Squashing {self.app_name}: '
                      f'"{self.start}"–"{self.end}"')
            return

        call_command(
            'django_squashmigrations',
            self.app_name,
            self.start,
            self.end,
            '--no-input',
            stdout=log
        )

    def post_processing(self):
        """
        post processing of squashed migration files,
        Drops part of django's squashmigration auto generated
        comments/commands that makes migration files unusable.
        """
        if self.dry_run:
            return

        self.load()
        try:
            os.mkdir(self.temp_directory)
        except FileExistsError:
            pass
        os.rename(self.file_name, self.temp_file_name)
        self._parse_generated_file()
        if not self.requires_action:
            return

        with open(self.temp_file_name, 'r') as read_file,\
             open(self.new_file_name, 'w') as write_file:
            stack_open = False
            line = "–"
            while line != "":
                line = read_file.readline()
                if 'RunPython(' in line:
                    stack_open = True
                    continue

                if stack_open and ')' in line:
                    stack_open = False
                    continue

                found = False
                for elem in self.migration_files_to_touch:
                    if elem.replacement_string in line:
                        found = True
                        index = line.find(elem.replacement_string)
                        next_space = line.find(
                            ' ',
                            index + len(elem.replacement_string)
                        )
                        if next_space == -1:
                            next_space = line.find(
                                ',',
                                index + len(elem.replacement_string)
                            )
                        if next_space == -1:
                            next_space = line.find(
                                '\n',
                                index + len(elem.replacement_string)
                            )
                        elem.replacement_string = line[index:next_space]
                        break

                if stack_open or 'code=' in line or '#' in line or found:
                    continue

                write_file.write(line)

        os.remove(self.temp_file_name)

    def process_data_migrations(self):
        """
        Generated data_migrations based on processed files.
        """
        for elem in self.migration_files_to_touch:
            module_name = elem.replacement_string.split(".")[-2]
            module = '.'.join(elem.replacement_string.split('.')[:-1])
            generator = DataMigrationGenerator(
                self.app_name, module_name,
                routines=[
                    Routine(
                        method=elem.replacement_string.split('.')[-1],
                        module=module,
                        module_name=f'mig_{module_name}',
                        file_path=elem.file_name,
                    )
                ],
                migration_dependencies=[module.replace('.migrations', '')],
                dry_run=self.dry_run,
            )
            generator.set_applied()


class MigrationSquash:
    def __init__(self, _loa: List[str], dry_run: bool = False):
        self.executor: MigrationExecutor = MigrationExecutor(connection)
        self.plan: MigrationPlan = []
        self.graph: MigrationGraph = {}
        self.get_migration_graph()
        self.parse_plan()
        self.list_of_apps = _loa
        self.dry_run = dry_run

    @property
    def log(self):
        return log

    def get_migration_graph(self):
        django_plan = self.executor.migration_plan(
            self.executor.loader.graph.leaf_nodes(),
            clean_start=True
        )
        self.plan = [i[0] for i in django_plan]

    def parse_plan(self):
        indices: Dict[str, int] = dict()
        last_key: str = ''
        for migration in self.plan:
            app = migration.app_label
            if app not in indices:
                indices[app] = 0
                self.graph[f'{app}_0'] = [migration]
            elif last_key == app:
                self.graph[f'{app}_{indices[app]}'].append(migration)

            elif len(list(self.graph.keys())) > 0 \
                    and self.graph[list(self.graph.keys())[-1]] != app:
                indices[app] += 1
                self.graph[f'{app}_{indices[app]}'] = [migration]
            else:
                self.graph[f'{app}_{indices[app]}'].append(migration)
            last_key = app

    def squash(self):
        for index, street in enumerate(self.graph.keys()):
            app_name: str = self.graph[street][0].app_label
            if len(self.graph[street]) > 1 and app_name in self.list_of_apps:
                from_id = self.graph[street][0].name
                to_id = self.graph[street][-1].name

                mig = MigrationManager(app_name, from_id, to_id, self.dry_run)
                mig.run()
                mig.post_processing()
                mig.process_data_migrations()
