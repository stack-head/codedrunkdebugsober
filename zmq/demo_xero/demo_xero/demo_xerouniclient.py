import logging
import signal
import argparse
from zmq import Context
from xero.uni.uniclientthread import UniClientThread
from xero.xero_constants import INITIAL_CONNECTION_TIME_SECS
from xero.exceptions import LostRemoteError
from demo_xero.setup_logging import configure_logging

logger = logging.getLogger(__name__)

keep_running = True

# Example usage:
# ./bin/demo_xerouniclient tcp://127.0.0.1:5550 compare --args '"uno", "dos"'
# ./bin/demo_xerouniclient tcp://127.0.0.1:5550 compare --kwargs '"str1":"uno", "str2":"dos"'
# ./bin/demo_xerouniclient tcp://127.0.0.1:5550 cut_video --args '"table_cam.mp4", "./output/bleh.mp4", "00:00:00", "00:02:00"'


def main():
    global keep_running

    configure_logging()
    # arg parser
    parser = argparse.ArgumentParser(description='Run task')
    parser.add_argument('ip', metavar='tcp://127.0.0.1:5550', type=str, help='target IP and port')
    parser.add_argument('task', type=str, help='name of the task')
    parser.add_argument('--args', metavar='args', type=str, required=False, help='arguments')
    parser.add_argument('--count', metavar='args', type=int, required=False, help='Number of times to repeat command, default is 1.  Set to -1 to call forever')
    parser.add_argument('--kwargs', metavar='kwargs', type=str, required=False, help='key-value arguments')
    parser.add_argument('--timeout', metavar='timeout', type=float, required=False, default=1.0, help='request timeout in seconds, default 1.0')
    args = parser.parse_args()
    arguments = eval('[%s]'%args.args if args.args is not None else '[]')
    kwarguments = eval('{%s}'%args.kwargs if args.kwargs is not None else '{}')
    count = args.count if args.count is not None else 1
    timeout = args.timeout

    # client
    context = Context()
    client = ConsoleUniClientThread(args.ip, context)

    # handle exit signals
    def handler(signum, frame):
        global keep_running
        print("Stopping client")
        client.stop()
        keep_running = False

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    print("Starting client")
    client.start()

    keep_running = True
    while keep_running:
        if client.is_connected():
            try:
                ret = client.rpc(args.task, arguments, kwarguments, timeout)
                #if ret isinstanceof Exception:
                if isinstance(ret, Exception):
                    raise ret
                else:
                    logger.debug("rpc reply: {}".format(repr(ret)))
            except LostRemoteError:
                print("Timed out waiting for rpc reply.")
            except Exception as e:
                logger.error("Worker experienced exception servicing RPC: {}".format(str(e)))
                pass
            if count > 0:
                count -= 1
                if count == 0:
                    break
        else:
            try:
                print("waiting for worker")
                client.wait_for_worker(INITIAL_CONNECTION_TIME_SECS)
            except LostRemoteError:
                print("Timed out waiting for worker")

    # TODO: consider making this part of stop.
    print("Shutting down")
    client.stop()
    client.shutdown()


class ConsoleUniClientThread(UniClientThread):

    def on_partial_message(self, msg):
        logger.debug("partial msg: {}".format(repr(msg)))

    def on_message(self, msg):
        logger.debug("final msg: {}".format(repr(msg)))

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
        print(traceback)
