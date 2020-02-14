import logging
from time import sleep
import unittest
import pytest
from tornado.ioloop import IOLoop

from xero.clients.console_uniclient_thread import ConsoleUniClientThread
from xero.clients.console_uniworker_thread import ConsoleUniWorkerThread
from xero.xero_constants import INITIAL_CONNECTION_TIME_SECS
from tests.clients.ErrorAssertUniClientThread import ErrorAssertUniClientThread


logger = logging.getLogger(__name__)


class TestZeroMQMessageRate(unittest.TestCase):

    TEST_ZMQ_ENDPOINT = "tcp://127.0.0.1:5556"
    RPC_MESSAGE_COUNT = 10000
    EMIT_MESSAGE_COUNT = 100000
    #TEST_ZMQ_ENDPOINT = "ipc:///tmp/test_message_rate"

    def setup_method(self, method):
        # Clear the IOLoop between each test.
        IOLoop.clear_current()

    @classmethod
    @pytest.mark.long
    #@pytest.mark.skip(reason="Replace client/worker threads that can detect and fail if disconnect occurs")
    def test_heartbeat_only(cls):
        # type: () -> None
        """
        Confirm a uniclient/uniworker combination will stay connected via heartbeat-no other scheduled communications
        """

        uniclient_thread = ErrorAssertUniClientThread(cls.TEST_ZMQ_ENDPOINT)
        uniclient_thread.start()

        uniworker_thread = ConsoleUniWorkerThread(cls.TEST_ZMQ_ENDPOINT)
        uniworker_thread.start()

        uniclient_thread.wait_for_worker(INITIAL_CONNECTION_TIME_SECS)
        # Wait for 60 seconds, make sure the client and worker remain connected.
        sleep(60)
        #sleep(30000)
        assert uniclient_thread.is_connected()
        assert uniworker_thread.is_connected()

        # Shut down the worker and client
        uniworker_thread.join()
        uniclient_thread.join()

    @classmethod
    @pytest.mark.long
    def test_zeromq_rpc_rate(cls):
        # type: () -> None

        uniclient_thread = ConsoleUniClientThread(cls.TEST_ZMQ_ENDPOINT)
        uniclient_thread.start()

        uniworker_thread = ConsoleUniWorkerThread(cls.TEST_ZMQ_ENDPOINT)
        uniworker_thread.start()

        uniclient_thread.wait_for_worker(INITIAL_CONNECTION_TIME_SECS)

#        meter = Meter()
        for i in range(0, cls.RPC_MESSAGE_COUNT):
            ret = uniclient_thread.rpc('compare', kwargs={
                'str1': "uno",
                'str2': "dos"
            })
            assert ret == {'equal': False}
#            meter.mark()
#            if 0 == i % 100:
#                logger.debug("Count: {}".format(meter.count))
#                logger.debug("1 sec rate: {}".format(meter.one_second_rate))
#                logger.debug("1 min rate: {}".format(meter.one_minute_rate))

#        count = meter.count
#        one_second_rate = meter.one_second_rate
#        logger.debug("Count: {}".format(count))
#        logger.debug("1 sec rate: {}".format(one_second_rate))

        # Shut down the worker and client
        uniworker_thread.join()
        uniclient_thread.join()

#        if one_second_rate < 650:
#            logger.warning("I would expect the one second message rate to stay above 650 on GLaDOS")

    @classmethod
    @pytest.mark.long
    def test_zeromq_emit_rate(cls):
        # type: () -> None
        uniclient_thread = ConsoleUniClientThread(cls.TEST_ZMQ_ENDPOINT)
        uniclient_thread.start()

        uniworker_thread = ConsoleUniWorkerThread(cls.TEST_ZMQ_ENDPOINT)
        uniworker_thread.start()

        uniclient_thread.wait_for_worker(INITIAL_CONNECTION_TIME_SECS)
        #uniworker_thread.wait_for_client(10.0)

        # Doing an RPC call is an easy/fast way to let the worker know the client is connected, active
        uniclient_thread.rpc('compare', kwargs={
            'str1': "uno",
            'str2': "dos"
        })

#        meter = Meter()
        total_receive_count = 0
        for i in range(0, cls.EMIT_MESSAGE_COUNT):
            uniworker_thread.emit({
                'str1': "uno",
                'str2': "dos"
            })
            received_emit_messages = uniclient_thread.get_sub_messages(timeout=0)
            receive_count = len(received_emit_messages)
#            meter.mark(receive_count)
            total_receive_count += receive_count
        logger.debug("Emitting done, waiting for {} more messages".format(cls.EMIT_MESSAGE_COUNT - total_receive_count))
        while total_receive_count < cls.EMIT_MESSAGE_COUNT:
            received_emit_messages = uniclient_thread.get_sub_messages(timeout=0.1)
            receive_count = len(received_emit_messages)
#            meter.mark(receive_count)
            total_receive_count += receive_count

        # Shut down the worker and client
        uniworker_thread.join()
        uniclient_thread.join()



