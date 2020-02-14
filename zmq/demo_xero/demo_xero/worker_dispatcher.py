import logging
from time import sleep
import pykka

logger = logging.getLogger(__name__)

def ping():
    return "pong"


def compare(str1, str2):
    if str1 == str2:
        return [True, 1]
    return [False, 2]


def return_none():
    return None


def take_too_long():
    sleep(10)
    return True


class WorkerDispatcher(object):

    def __init__(self, send_reply_cb):
        self._send_reply_cb = send_reply_cb

    def work_time_succeed(self, work_time):
        # type: (float) -> None
        _dispatcher_actor = UniWorkerActor.start().proxy()
        try:
            _dispatcher_actor.work_time_succeed(work_time, self._send_reply_cb).get(timeout=0)
        except pykka.Timeout:
            # This means the actor hasn't finished yet.  Just eat the exception and move on.
            pass

    def work_time_fail(self, work_time):
        # type: (float) -> None
        _dispatcher_actor = UniWorkerActor.start().proxy()
        try:
            _dispatcher_actor.work_time_fail(work_time, self._send_reply_cb).get(timeout=0)
        except pykka.Timeout:
            # This means the actor hasn't finished yet.  Just eat the exception and move on.
            pass


class UniWorkerActor(pykka.ThreadingActor):

    def __init__(self):
        super(UniWorkerActor, self).__init__()

    def work_time_succeed(self, sleep_time, reply_future):
        sleep(sleep_time)
        reply_future(True)

    def work_time_fail(self, sleep_time, reply_future):
        sleep(sleep_time)
        reply_future(False)
