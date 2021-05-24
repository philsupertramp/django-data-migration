import pytest
from tests.utils import setup_django, teardown_django


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    setup_django()


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config):
    teardown_django()
