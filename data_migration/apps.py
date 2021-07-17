from django.conf import settings
from django.apps import AppConfig

from data_migration.settings import internal_settings


class DataMigrationsConfig(AppConfig):
    name = 'data_migration'
    verbose_name = 'Django data migrations'

    def ready(self):
        internal_settings.update(settings)
