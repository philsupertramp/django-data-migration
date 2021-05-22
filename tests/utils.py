import os
from typing import Optional
from unittest import TestCase


class FileTestCase(TestCase):
    target = ''

    def clean_directory(self):
        dir_path = os.path.join(self.target, 'out/data_migrations')
        files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f != '.gitkeep']
        for file in files:
            os.remove(file)
        os.removedirs(os.path.join(self.target, 'out/data_migrations'))

    def has_file(self, name: str) -> bool:
        dir_path = os.path.join(self.target, 'out/data_migrations')
        try:
            for f in os.listdir(dir_path):
                if f == name:
                    return True
        except FileNotFoundError:
            pass
        return False

    def get_file(self, name: str) -> Optional[str]:
        dir_path = os.path.join(self.target, 'out/data_migrations')
        for f in os.listdir(dir_path):
            if f == name:
                with open(os.path.join(dir_path, f), 'r') as file:
                    content = file.read()
                return content
        return None
