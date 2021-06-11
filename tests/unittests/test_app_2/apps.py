from django.apps import AppConfig


class TestApp2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tests.unittests.test_app_2'
    label = 'test_app_2'
