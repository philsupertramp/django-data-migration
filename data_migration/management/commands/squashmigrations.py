from django.apps import apps
from django.core.management import CommandError
from django.core.management.commands.squashmigrations import Command as Migrate

from data_migration.services.squasher import MigrationSquash


class Command(Migrate):
    """Extended `squashmigrations` management command."""

    def add_arguments(self, parser):  # noqa D102
        parser.add_argument(
            '--extract-data-migrations',
            dest='extract_data_migrations',
            action='store_true',
            help='Minimize current migration tree and emplace data migrations',
        )
        super().add_arguments(parser)

    def handle(self, **options):  # noqa D102
        app_label = options['app_label']
        extract_data_migrations = options['extract_data_migrations']
        # Validate app_label.
        try:
            apps.get_app_config(app_label)
        except LookupError as err:
            raise CommandError(str(err))

        if extract_data_migrations:
            squasher = MigrationSquash(app_label)
            squasher.squash()
            return squasher.log.log
        else:
            return super().handle(**options)
