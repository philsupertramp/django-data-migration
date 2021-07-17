from unittest import TestCase


from data_migration.settings import DataMigrationSettings, reload


class SettingsTestCase(TestCase):
    def test_uses_user_setting(self):
        from django.conf import settings as django_settings
        settings = DataMigrationSettings(django_settings)
        self.assertEqual(settings.SQUASHABLE_APPS, django_settings.DATA_MIGRATION.get('SQUASHABLE_APPS'))

    def test_update(self):
        from django.conf import settings as django_settings
        settings = DataMigrationSettings(django_settings)
        settings.update({'DATA_MIGRATION': {'SQUASHABLE_APPS': ['foo']}})

        self.assertEqual(settings.SQUASHABLE_APPS, ['foo'])

    def test_reload(self):
        from django.conf import settings as django_settings

        settings = DataMigrationSettings(None, {'SQUASHABLE_APPS': ['foo']})

        self.assertEqual(settings.SQUASHABLE_APPS, ['foo'])

        settings.reload(django_settings)

        self.assertNotEqual(settings.SQUASHABLE_APPS, ['foo'])

    def test_reload_on_signal(self):
        reload()