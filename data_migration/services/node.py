from django.apps.registry import Apps
from django.db import models, connections, DatabaseError
from django.utils import timezone


class classproperty:
    """
    Decorator that converts a method with a single cls argument into a property
    that can be accessed directly from the class.
    """
    def __init__(self, method=None):
        self.fget = method

    def __get__(self, instance, cls=None):
        return self.fget(cls)

    def getter(self, method):
        self.fget = method
        return self



class AlreadyAppliedError(Exception):
    def __init__(self, node: 'Node.Node'):
        super().__init__(f'Node {node} already applied. Do not reapply them!')


class Node:
    """
    This is literally the same as django's MigrationRecorder
    """
    _node_model = None

    @classproperty
    def Node(cls):
        """
        bypass missing appconfig
        """
        if cls._node_model is None:
            class NodeClass(models.Model):
                app_name = models.CharField(max_length=255)
                name = models.CharField(max_length=255, unique=True)
                created_at = models.DateTimeField()

                class Meta:
                    apps = Apps()
                    app_label = 'data_migration'
                    db_table = 'data_migrations'
                    get_latest_by = 'created_at'

            cls._node_model = NodeClass
        return cls._node_model

    def __init__(self, name, app_name, *args, **kwargs):
        self.pk = kwargs.get('pk')
        self.name = name
        self.app_name = app_name
        self.created_at = kwargs.get('created_at')

    @property
    def is_applied(self):
        return bool(self.created_at and self.pk)

    def apply(self) -> None:
        if self.pk:
            raise AlreadyAppliedError(self)

        self.ensure_table()
        self.created_at = timezone.now()

        obj = self.Node(name=self.name, app_name=self.app_name, created_at=self.created_at)
        obj.save()
        self.pk = obj.pk
        self.created_at = obj.created_at

    @classproperty
    def qs(self) -> models.Manager:
        return self.Node.objects

    def has_table(self):
        with connections['default'].cursor() as cursor:
            tables = connections['default'].introspection.table_names(cursor)
        return self.Node._meta.db_table in tables

    def ensure_table(self):
        if self.has_table():
            return
        # Make the table
        try:
            with connections['default'].schema_editor() as editor:
                editor.create_model(self.Node)
        except DatabaseError:
            raise Exception('Table not "data_migrations" creatable')
