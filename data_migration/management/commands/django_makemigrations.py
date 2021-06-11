from django.core.management.commands.makemigrations import Command as Migrate


class Command(Migrate):
    """Alias for default `makemigrations` command provided by Django."""

    def handle(self, *args, **options):  # noqa D102
        return super().handle(*args, **options)
