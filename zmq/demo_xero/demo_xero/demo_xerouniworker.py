import logging
import datetime
import dateutil.parser
import signal
from time import sleep
import traceback
import argparse
from zmq import Context

from xero.uni.uniworker import UniWorker

# include all modules from modules directory
from demo_xero.setup_logging import configure_logging
from demo_xero.worker_dispatcher import WorkerDispatcher, ping, compare, return_none

try:
    from typing import Any, Dict, List
except ImportError:
    Any = Dict = None

logger = logging.getLogger(__name__)


class TrivialUniWorker(UniWorker):

    def __init__(self, endpoint, context):
        super(TrivialUniWorker, self).__init__(endpoint, context)
        self._dispatcher = WorkerDispatcher(self.send_reply)

        self._methods = {
            'ping': ping,
            'compare': compare,
            'return_none': return_none,
            'slow_succeed': self._dispatcher.work_time_succeed,
            'slow_fail': self._dispatcher.work_time_fail
        }

    def on_log_event(self, event, message):
        print(message)

    def do_work(self, name, args, kwargs):
        # type: (str, List[Any], Dict[Any, Any]) -> None

        try:
            if name in self._methods:
                self.send_reply('started', partial=True)
                result = self._methods[name](*args, **kwargs)
                self.send_reply(result)
            else:
                print("called unknown method '{}'".format(name))
                raise Exception('method {} not found'.format(name))

        except Exception as e:
            # Capture exceptions and send them back to the client
            self.send_reply(e, exception=True)



def main():
    # arg parser
    configure_logging()
    parser = argparse.ArgumentParser(description='Worker')
    parser.add_argument('target', metavar='tcp://127.0.0.1:5550', type=str, help='target IP and port ex. tcp://127.0.0.1:5550')
    parser.add_argument('--groups', metavar='name', type=str, nargs='+', help='list of groups')
    args = parser.parse_args()

    context = Context()

    print("starting worker connected to IP '{}'".format(args.target))
    worker = TrivialUniWorker(args.target, context)

    # handle exit signals
    def handler(signum, frame):
        print('worker is exiting, received signum: {}'.format(signum))
        worker.stop()
        worker.shutdown()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    worker.run()
    worker.shutdown()


