import logging
import pytest


logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        '--runlong', help='Run long running tests.', action='store_true'
        )


def pytest_configure(config):
    config.addinivalue_line("markers", "long: mark test as long to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runlong"):
        # --runlong given in cli: do not skip slow tests
        return
    skip_long = pytest.mark.skip(reason="need --runlong option to run")
    for item in items:
        if "long" in item.keywords:
            item.add_marker(skip_long)


@pytest.fixture(scope="session", autouse=True)
def set_up(request):
    logger.debug("SETUP before all tests")
    request.addfinalizer(tear_down)


def tear_down():
    logger.debug("TEARDOWN after all tests")


