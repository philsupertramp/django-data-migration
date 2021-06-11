import os.path


this_dir = os.path.dirname(__file__)


class ResetDirectoryContext:
    targets = ['migrations', 'data_migrations']
    protected_files = [
        '0001_initial.py',     '0004_customer_is_active.py',  '0007_remove_customer_address.py',
        '0002_split_name.py',  '0005_customer_address.py',    '0008_customer_is_business.py',
        '0003_mmodel.py',      '0006_address_line_split.py',  '__init__.py',

    ]

    def __enter__(self):
        return True

    def __exit__(self, exc_type, exc_val, exc_tb):
        for target in self.targets:
            dir_path = os.path.join(this_dir, target)
            try:
                files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f not in self.protected_files and os.path.isfile(os.path.join(dir_path, f))]
            except FileNotFoundError:
                continue
            for file in files:
                os.remove(file)

