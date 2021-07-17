class classproperty:
    """
    Decorator that converts a method with a single cls argument into a property
    that can be accessed directly from the class.
    """
    def __init__(self, method=None):
        self.fget = method

    def __get__(self, instance, cls=None):
        return self.fget(cls)


class AlreadyAppliedError(Exception):
    def __init__(self, node: 'Node.Node'):
        super().__init__(f'Node {node} already applied. Do not reapply them!')


class DatabaseError(Exception):
    def __init__(self, message):
        super().__init__(message)


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
            from django.apps.registry import Apps
            from django.db import models

            class NodeClass(models.Model):
                app_name = models.CharField(max_length=255)
                name = models.CharField(max_length=255)
                created_at = models.DateTimeField()

                class Meta:
                    apps = Apps()
                    app_label = 'data_migration'
                    db_table = 'data_migrations'
                    get_latest_by = 'created_at'
                    constraints = [
                        models.UniqueConstraint(
                            fields=['app_name', 'name'],
                            name='unique_name_for_app'
                        )
                    ]

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
        from django.utils import timezone
        self.created_at = timezone.now()

        obj = self.Node(
            name=self.name,
            app_name=self.app_name,
            created_at=self.created_at
        )
        obj.save()
        self.pk = obj.pk
        self.created_at = obj.created_at

    @property
    def qs(self):
        return self.Node.objects

    def exists(self):
        self.ensure_table()
        return self.qs.filter(
            app_name=self.app_name,
            name=self.name
        ).exists()

    @classmethod
    def flush(cls):
        return cls.get_qs().delete()

    @classmethod
    def get_qs(cls):
        node = cls('', '')
        node.ensure_table()
        return node.qs.all()

    def has_table(self):
        from django.db import connections
        with connections['default'].cursor() as cursor:
            tables = connections['default'].introspection.table_names(cursor)
        return self.Node._meta.db_table in tables

    def ensure_table(self):
        if self.has_table():
            return
        from django.db import connections, DatabaseError as DjDatabaseError
        # Make the table
        try:
            with connections['default'].schema_editor() as editor:
                editor.create_model(self.Node)
        except DjDatabaseError as ex:
            raise DatabaseError(
                f'Table "data_migrations" not creatable ({str(ex)}'
            )
