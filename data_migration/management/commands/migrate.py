from django.apps import apps
from django.core.management import CommandError
from django.core.management.commands.migrate import Command as Migrate

from data_migration.services.graph import Graph


class Command(Migrate):
    """
    Extended migrate command.

    Allows forward and backward migration of data/regular migrations
    """

    def add_arguments(self, parser):  # noqa D102
        parser.add_argument(
            '--data-only', action='store_true', dest='data_migration',
            help='Applies data migrations',
        )
        super().add_arguments(parser)

    def handle(self, *args, **options):  # noqa D102
        # extract parameters

        if options['app_label']:
            # Validate app_label.
            app_label = options['app_label']
            try:
                apps.get_app_config(app_label)
            except LookupError as err:
                raise CommandError(str(err))

            data_migrations = Graph.from_dir(app_label)
            data_migrations.apply(options.get('migration_name'))

        if not options['data_migration']:
            return super().handle(*args, **options)
