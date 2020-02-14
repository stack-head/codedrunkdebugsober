from time import sleep
import logging
import unittest
import pytest
from zmq import Context
from xero.exceptions import LostRemoteError
from xero.clients.console_uniclient_thread import ConsoleUniClientThread
from xero.xero_constants import INITIAL_CONNECTION_TIME_SECS

from tornado.ioloop import IOLoop

logger = logging.getLogger(__name__)


class TestUniClientStandalone(unittest.TestCase):

    TEST_ZMQ_ENDPOINT = "tcp://127.0.0.1:5556"

    def setup_method(self, method):
        # See https://www.tornadoweb.org/en/stable/ioloop.html#tornado.ioloop.IOLoop.clear_current
        # Clear the IOLoop between each test.
        IOLoop.clear_current()

    @classmethod
    def test_uniclient_startup_shutdown(cls):
        # type: () -> None
        uniclientThread = ConsoleUniClientThread(cls.TEST_ZMQ_ENDPOINT, Context())
        uniclientThread.start()
        uniclientThread.join()

    @classmethod
    def test_uniclient_startup_shutdown_delay(cls):
        # type: () -> None

        #IOLoop.clear_current()

        uniclientThread = ConsoleUniClientThread(cls.TEST_ZMQ_ENDPOINT, Context())
        uniclientThread.start()
        sleep(5)
        uniclientThread.join()
        #uniclientThread.stop()
        #uniclientThread.shutdown()

    @classmethod
    def test_uniclient_wait_for_worker_no_connect_shutdown(cls):
        # type: () -> None

        #IOLoop.clear_current()

        uniclientThread = ConsoleUniClientThread(cls.TEST_ZMQ_ENDPOINT, Context())
        uniclientThread.start()
        with pytest.raises(LostRemoteError):
            uniclientThread.wait_for_worker(INITIAL_CONNECTION_TIME_SECS)
        uniclientThread.join()
        #uniclientThread.stop()
        #uniclientThread.shutdown()


