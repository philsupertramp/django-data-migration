from django.core.management import BaseCommand

from data_migration.services.squasher import MigrationSquash
from data_migration.settings import internal_settings as data_migration_settings


class Command(BaseCommand):
    """
    Extended migrate command.

    Allows forward and backward migration of data/regular migrations
    """

    def add_arguments(self, parser):  # noqa D102
        parser.add_argument(
            '--app_labels', nargs='?', dest='app_labels',
            help='App label of an application to synchronize the state.',
        )
        parser.add_argument(
            '--all', '-a', action='store_true', dest='squash_all',
            help='Squash all apps.',
        )
        super().add_arguments(parser)

    def handle(self, *args, **options):  # noqa D102
        # extract parameters
        apps_to_squash = options.get('app_labels')
        if apps_to_squash is None and options['squash_all']:
            apps_to_squash = data_migration_settings.SQUASHABLE_APPS

        MigrationSquash(apps_to_squash).squash()
