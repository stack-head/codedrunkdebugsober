import logging

from xero.uni.uniclient import UniClient

logger = logging.getLogger(__name__)


class ConsoleUniClient(UniClient):

    def on_partial_message(self, msg):
        #logger.debug("partial msg: {}".format(repr(msg)))
        print("partial msg: {}".format(repr(msg)))

    def on_message(self, msg):
        #logger.debug("final msg: {}".format(repr(msg)))
        print("final msg: {}".format(repr(msg)))

    def on_timeout(self):
        no_responses = []
        if no_responses:
            print("Timeout! No responses from: {}".format(repr(no_responses)))
        else:
            print('Timeout!')

    def on_error_message(self, msg):
        print("Error message: {}".format(msg))

    def on_exception_message(self, cls, message, traceback):
        print("{} with message: {}".format(cls, message))
        print(traceback.decode('utf-8'))
