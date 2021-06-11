"""public helpers of package."""
import os


def get_package_version_string():
    """:return: version string of package."""
    name = 'data_migration'
    version = os.getenv('VERSION', '0.0.1a')
    return f'{name} {version}'
