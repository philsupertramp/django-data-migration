import os.path

from tests.unittests.test_app.helper import ResetDirectoryContext


this_dir = os.path.dirname(__file__)


class ResetDirectory2Context(ResetDirectoryContext):
    targets = ['migrations', 'data_migrations']
    protected_files = [
        '0001_initial.py', '0004_customer_is_active.py',
        '0007_remove_customer_address.py',
        '0002_split_name.py', '0005_customer_address.py',
        '0008_customer_is_business.py', '0003_mmodel.py',
        '0006_address_line_split.py', '__init__.py',
    ]
