from django.core.management.commands.squashmigrations import Command as Migrate


class Command(Migrate):
    """
    Alias for default `squashmigrations` command provided by Django
    """
    def handle(self, **options):
        return super().handle(**options)

