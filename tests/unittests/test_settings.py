from unittest import TestCase, mock

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

    def test_reload_fails_silently(self):
        settings = DataMigrationSettings(None, {'SQUASHABLE_APPS': ['foo']})

        settings.reload(None)

        self.assertEqual(settings.SQUASHABLE_APPS, ['foo'])

    @mock.patch('data_migration.settings.DataMigrationSettings.update')
    def test_reload_on_signal(self, update_mock):
        update_payload = {'SQUASHABLE_APPS': ['foo']}
        reload(None, 'DATA_MIGRATION', update_payload)

        update_mock.assert_called_once()
        update_mock.assert_called_with(update_payload)
        update_mock.reset_mock()

        reload(None, 'FOO', update_payload)

        update_mock.assert_not_called()
