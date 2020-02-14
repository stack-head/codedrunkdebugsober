from threading import Thread, current_thread
from abc import ABCMeta

from xero.uni.uniclient import UniClient

try:
    from typing import Any, List, Optional, Tuple, Union
except ImportError:
    Any = None
    List = None
    Optional = None
    Tuple = None
    Union = None


class UniClientThread(UniClient, Thread):
    """
    Convenience class to wrap around UniClient.  UniClient needs to make a blocking call to run the "IOLoop" to
    send/receive ZMQ messages, this will wrap that blocking call in a dedicated thread.
    """

    __metaclass__ = ABCMeta

    def __init__(self, endpoint, context=None):
        # type: (str, zmq.Context) -> None
        """
        :param endpoint: ZeroMQ endpoint to bind to.
        :param context: ZeroMQ Context.
        """
        # Worker and Thread have different init signatures, so we'll call them separately.
        UniClient.__init__(self, endpoint, context)
        Thread.__init__(self)

    def run(self):
        # type: () -> None
        """
        Start the IOLoop, a blocking call to send/recv ZMQ messsages until the IOLoop is stopped.
        Note: The name of this function needs to stay the same so UniClientThread's run() is overridden with this function.
        """
        self.name = 'uniclientthread'
        super(UniClientThread, self).run()

    def join(self, timeout=None):
        UniClient.stop(self)
        UniClient.shutdown(self)
        super(UniClientThread, self).join(timeout)

