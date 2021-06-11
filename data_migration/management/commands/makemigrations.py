from django.core.management.commands.makemigrations import Command as Migrate

from data_migration.services.file_generator import DataMigrationGenerator


class Command(Migrate):
    """Extended makemigrations command."""

    def add_arguments(self, parser):  # noqa D102
        parser.add_argument(
            '--data-only', action='store_true', dest='data_migration',
            help='Creates a data migration file.',
        )
        super().add_arguments(parser)

    def handle(self, *app_labels, **options):  # noqa D102
        create_empty_data_migration = options.get('data_migration')
        if create_empty_data_migration:
            is_dry_run = options.get('dry_run')
            return 'Generated files: ' + ', '.join([
                DataMigrationGenerator(
                    app,
                    readable_name=options.get('name'),
                    set_header=options.get('include_header', True),
                    empty=options.get('empty', False),
                    dry_run=is_dry_run
                ).file_name for app in app_labels])

        else:
            return super().handle(*app_labels, **options)
