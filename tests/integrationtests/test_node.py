import unittest

from data_migration.services.node import classproperty


class NodeTestCase(unittest.TestCase):
    def test_classproperty_class_can_be_used_without_django(self):
        class WrapperClass:
            _model_class = None

            @classproperty
            def InnerClass(cls):
                if cls._model_class is None:
                    from django.db import models
                    from django.apps.registry import Apps

                    class DjangoModelClass(models.Model):
                        value = models.TextField()

                        class Meta:
                            apps = Apps()
                            app_label = 'model_class'
                            db_table = 'model_class'
                    cls._model_class = DjangoModelClass
                return cls._model_class

            def __init__(self, name):
                self.name = name

            @property
            def qs(self):
                return self._model_class.objects

            def __str__(self):
                return self.name

        wrapper = WrapperClass('wrapper')

        self.assertEqual(str(wrapper), 'wrapper')
