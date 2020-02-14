from threading import Thread, current_thread
from abc import ABCMeta
import zmq

from xero.uni.uniworker import UniWorker


class UniWorkerThread(UniWorker, Thread):
    """
    Convenience class to wrap around UniWorker.  UniWorker needs to make a blocking call to run the "IOLoop" to
    send/receive ZMQ messages, this will wrap that blocking call in a dedicated thread.
    """

    __metaclass__ = ABCMeta

    def __init__(self, endpoint, context=None):
        # type: (str, zmq.Context) -> None
        # Worker and Thread have different init signatures, so we'll call them separately.
        UniWorker.__init__(self, endpoint, context)
        Thread.__init__(self)

    def run(self):
        self.name = 'uniworkerthread'
        super(UniWorkerThread, self).run()

    def join(self, timeout=None):
        UniWorker.stop(self)
        UniWorker.shutdown(self)
        super(UniWorkerThread, self).join(timeout)
