import os.path

from tests.utils import ResetDirectoryMixin

this_dir = os.path.dirname(__file__)


class ResetDirectoryContext(ResetDirectoryMixin):
    targets = ['migrations', 'data_migrations']
    protected_files = ['__init__.py', '0001_first.py', '0002_add_name.py']
    this_dir = this_dir
