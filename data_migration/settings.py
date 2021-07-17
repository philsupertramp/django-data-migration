from typing import Dict, Optional

from django.core.signals import setting_changed

DATA_MIGRATION_DEFAULTS = {
    "SQUASHABLE_APPS": []
}


class DataMigrationSettings(object):
    def __init__(self, user_settings=None, defaults: Optional[Dict] = None):
        if defaults is None:
            defaults = DATA_MIGRATION_DEFAULTS

        self.settings = defaults.copy()
        if user_settings:
            self.update(user_settings)

    def update(self, settings):
        try:
            self.settings.update(getattr(settings, 'DATA_MIGRATION'))
        except AttributeError:
            self.settings.update(settings.get('DATA_MIGRATION', {}))

    def reload(self, settings):
        try:
            _user_settings = getattr(settings, 'DATA_MIGRATION')
            self.settings = _user_settings
        except AttributeError:
            pass

    def __getattr__(self, item):
        return self.settings[item]


internal_settings = DataMigrationSettings(None)


def reload(sender, setting, value, *args, **kwargs):
    if setting == 'DATA_MIGRATION':
        internal_settings.update(value)


setting_changed.connect(reload)
