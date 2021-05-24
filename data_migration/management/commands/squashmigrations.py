from django.core.management.commands.squashmigrations import Command as Migrate


class Command(Migrate):
    """
    Extended `squashmigrations` management command.
    """
    def handle(self, **options):
        return super().handle(**options)

