import logging
import pytest
import unittest

from xero.uni.uniclientthread import UniClientThread

logger = logging.getLogger(__name__)


class ErrorAssertUniClientThread(UniClientThread):

    def on_partial_message(self, msg):
        logger.debug("partial msg: {}".format(repr(msg)))

    def on_message(self, msg):
        logger.debug("final msg: {}".format(repr(msg)))

    def on_timeout(self):
        pytest.fail("UniClientThread timed out")

    def on_error_message(self, msg):
        print("Error message: {}".format(msg))
        assert False

    def on_exception_message(self, cls, message, traceback):
        print("{} with message: {}".format(cls, message))
        print(traceback)
        assert False

