from time import sleep
import logging
import unittest
import pytest
from zmq import Context
from tornado.ioloop import IOLoop
from xero.clients.console_uniworker_thread import ConsoleUniWorkerThread

logger = logging.getLogger(__name__)


class TestUniWorkerStandalone(unittest.TestCase):

    TEST_ZMQ_ENDPOINT = "tcp://127.0.0.1:5556"

    def setup_method(self, method):
        # Clear the IOLoop between each test.
        IOLoop.clear_current()

    @classmethod
    def test_uniworker_startup_shutdown(cls):
        # type: () -> None
        workerThread = ConsoleUniWorkerThread(cls.TEST_ZMQ_ENDPOINT, Context())
        workerThread.start()
        workerThread.join()

    @classmethod
    def test_uniworker_startup_shutdown_delay(cls):
        # type: () -> None
        workerThread = ConsoleUniWorkerThread(cls.TEST_ZMQ_ENDPOINT, Context())
        workerThread.start()
        sleep(5)
        workerThread.join()

