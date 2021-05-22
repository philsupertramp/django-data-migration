import os.path


this_dir = os.path.dirname(__file__)


class ResetDirectoryContext:
    targets = ['migrations', 'data_migrations']
    protected_files = ['__init__.py', '0001_first.py']

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

