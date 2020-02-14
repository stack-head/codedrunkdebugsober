import logging
from queue import Queue, Empty
from threading import Event, Lock
from abc import ABCMeta, abstractmethod
import msgpack
import zmq
from tornado.ioloop import IOLoop, PeriodicCallback

from zmq.eventloop.zmqstream import ZMQStream
from xero.util.xero_serialization import XeroSerializer
from xero.exceptions import LostRemoteError
from xero.xero_constants import *

try:
    from typing import Any, Dict, List, Optional, Tuple, Union
except ImportError:
    Any = None
    List = None
    Optional = None
    Tuple = None
    Union = None

logger = logging.getLogger(__name__)


class UniClient(object):
    """
    Implementation of "simple" ZeroMQ Paranoid Pirate communication scheme.  This class is the ROUTER, and performs the
    "request" in RPC calls.  By design, only supports one remote worker (DEALER) in order to keep example simple.
    Supports a very basic RPC interface, using MessagePack for encoding/decoding.
    """

    __metaclass__ = ABCMeta

    def __init__(self, endpoint, context=None):
        # type: (str, zmq.Context) -> None
        """
        :param endpoint: ZeroMQ endpoint to bind to.
        :param context: ZeroMQ Context.
        """
        self._q_received_messages = Queue()   # type: Queue[Any]
        self._q_sub_messages = Queue()  # type: Queue[Any]
        self._lock = Lock()

        context = context or zmq.Context.instance()
        socket = context.socket(zmq.ROUTER)
        socket.bind(endpoint)

        self._stream = ZMQStream(socket, IOLoop())
        self._stream.on_recv(self._on_message)

        self._worker_rep = None  # type: Optional[WorkerRep]
        self._connected_event = Event()
        self._hb_check_timer = PeriodicCallback(self._heartbeat, HB_INTERVAL)
        self._hb_check_timer.start()
        self._keep_running = True

    def run(self):
        # type: () -> None
        """
        Start the IOLoop, a blocking call to send/recv ZMQ messsages until the IOLoop is stopped.
        Note: The name of this function needs to stay the same so UniClientThread's run() is overridden with this function.
        """
        # Handle situation where stop() is called before run() activates
        # This blocks until stop is called
        if self._keep_running:
            self._stream.io_loop.start()

    def stop(self):
        # type: () -> None
        """
        Stop the IOLoop.  Note: this overrides the base class (Thread)'s implementation of stop, so don't rename
        this function.
        """
        with self._lock:
            self._keep_running = False
            if self._stream is not None:
                self._stream.io_loop.stop()

    def shutdown(self):
        # type: () -> None
        """
        Shutdown the uniclient, stopping all timers and unbinding from the ZMQ socket.
        """
        with self._lock:
            if self._stream is not None:
                self._stream.on_recv(None)
                self._stream.socket.setsockopt(zmq.LINGER, 0)
                self._stream.close()
                self._stream = None
                self._worker_rep = None

    def wait_for_worker(self, timeout):
        # type: (float) -> None
        """
        Wait for the client to establish a connection with the remote worker.
        Will return immediately if already connected.
        :param timeout: Max time, in seconds, to wait for the connection to establish.
        """
        event_status = self._connected_event.wait(timeout)
        if not event_status:
            raise LostRemoteError("No worker is connected.")

    def is_connected(self):
        # type: () -> bool
        """
        Returns whether client is connected to a worker.
        :return: A boolean flag to indicate whether a connection to the worker is established.
        """
        return self._worker_rep is not None

    def rpc(self, method, args=None, kwargs=None, timeout=RPC_TIMEOUT):
        # type: (str, List[Any], Optional[Dict[str,Any]], Optional[float]) -> Any
        """
        Call RPC 'method' on remote worker.
        :param method: String indicating which remote method to call.
        :param args: Arguments to provide to remote method.
        :param kwargs: Key arguments to provide to remote method.
        :param timeout: RPC call timeout, in seconds.  Use None for no timeout.
        """
        data = [method.encode('utf-8'),
                msgpack.packb([] if args is None else args, default=XeroSerializer.encoder),
                msgpack.packb({} if kwargs is None else kwargs, default=XeroSerializer.encoder)]
        self._request(data)
        try:
            ret = self._q_received_messages.get(timeout=timeout)
        except Empty:
            self._unregister_worker()
            raise LostRemoteError("Worker failed to reply to RPC call in time.")
        return ret

    def get_sub_message(self, timeout=None):
        # type: (float) -> Any
        return self._q_sub_messages.get(timeout=timeout)

    def get_sub_messages(self, timeout=None):
        # type: (float) -> List[Any]
        ret = []
        try:
            while True:
                ret.append(self._q_sub_messages.get(timeout=timeout))
        except Empty:
            # Out of entries.
            pass
        return ret

    def _on_reply_timeout(self):
        # type: () -> None
        """
        This gets called when a ZeroMQ message is sent and no reply comes within the specified timeout.
        """
        self.timed_out = True
        self._timeout_handle = None
        self._stream.io_loop.stop()
        self.on_timeout()

    def _request(self, msg):
        # type: (List[bytes]) -> None
        """
        Send msgpack encoded message via ZeroMQ.
        :param msg: msgpack encoded message.
        """
        # prepare full message
        with self._lock:
            if self._worker_rep is not None:
                to_send = [self._worker_rep.id]
                to_send.extend([UNI_CLIENT_HEADER, WORKER_REQUEST])
                to_send.extend(msg)

                # OK, calling this in the callback is extremely important, so be careful about modifying it.
                # All the other ZMQ message sends happen in the context of this thread, which means they work fine.
                # However, this call will typically happen in the context of whatever thread communicates with this
                # thread to issue RPC calls.  That means if you don't send the messages in the context of the callback,
                # they won't get sent immediately-they'll get sent when the IOloop starts again.  This will look like
                # really slow ZeroMQ sends.
                self._stream.io_loop.add_callback(lambda x: self._stream.send_multipart(x), to_send)
            else:
                raise LostRemoteError("No worker is connected.")

    def on_log_event(self, event, message):
        # type: (str, str) -> None
        """
        Logs events, designed to be overridden if helpful.
        :param event: The uniclient event type.
        :param message: The message.
        """
        logger.debug(event + message)

    def _on_message(self, message):
        # type: (List[bytes]) -> None
        """
        Processes a received ZeroMQ message.
        :param message: List of strings in the format:
            [ ZMQ Worker ID, Message Header, StrMessagePart1, StrMessagePart2...]
        """
        return_address = message.pop(0)
        cmd = message.pop(0)

        worker_cmds = {
            WORKER_READY: self._on_worker_ready,
            WORKER_PARTIAL_REPLY: self._on_worker_partial_reply,
            WORKER_FINAL_REPLY: self._on_worker_final_reply,
            WORKER_EXCEPTION: self._on_worker_final_reply,
            WORKER_EMIT: self._on_worker_emit,
            WORKER_HEARTBEAT: self._on_worker_heartbeat,
            WORKER_DISCONNECT: self._on_worker_disconnect,
        }
        if cmd in worker_cmds:
            fnc = worker_cmds[cmd]
            fnc(return_address, message)
        else:
            logger.error("Received worker message with unrecognized header: {}.".format(cmd))

    def _on_worker_ready(self, return_address, message):
        # type: (bytes, List[bytes]) -> None
        """
        This gets called when a worker tells us it's ready to receive messages.  This should be the first message we receive
        from a new worker.
        :param return_address: List of return addresses/Worker IDs.
        :param message: ZeroMQ message.
        :return:
        """
        worker_id = return_address
        self._register_worker(worker_id)

    def _on_worker_partial_reply(self, return_address, message):
        # type: (bytes, List[bytes]) -> None
        """
        Process a received worker's ZMQ partial reply.  It will be forwarded to the requesting client.
        :param return_address: Worker ZMQ ID.
        :param message: The worker's reply message.
        """
        message.pop(0)
        try:
            msg = msgpack.unpackb(message[0], raw=False)
        except (msgpack.OutOfData, msgpack.ExtraData):
            msg = message[0]
        self.on_partial_message(msg)

    def _on_worker_final_reply(self, return_address, message):
        # type: (bytes, List[bytes]) -> None
        """
        Process a received worker's ZMQ final reply.  It will be forwarded to the requesting client.
        :param return_address: Worker ZMQ ID.
        :param message: The worker's reply message.
        """

        with self._lock:
            if self._worker_rep is None or return_address != self._worker_rep.id:
                logger.info("Got final reply from unknown worker, discarding")
                return

            if return_address == self._worker_rep.id:
                self._worker_rep.on_heartbeat()

        message.pop(0)
        try:
            msg = msgpack.unpackb(message[0], object_hook=XeroSerializer.decoder, raw=False)
        except (msgpack.OutOfData, msgpack.ExtraData):
            msg = message[0]
        self._q_received_messages.put_nowait(msg)

    def _on_worker_emit(self, return_address, message):
        # type: (bytes, List[bytes]) -> None

        with self._lock:
            if self._worker_rep is not None:
                ret_id = return_address
                if ret_id == self._worker_rep.id:
                    self._worker_rep.on_heartbeat()
                else:
                    logger.error("Received heartbeat message from unknown worker.")

        message.pop(0)
        try:
            msg = msgpack.unpackb(message[0], object_hook=XeroSerializer.decoder, raw=False)
        except (msgpack.OutOfData, msgpack.ExtraData):
            msg = message[0]
        self._q_sub_messages.put(msg)

    def _on_worker_heartbeat(self, return_address, message):
        # type: (bytes, List[bytes]) -> None
        """
        Process worker ZMQ heartbeat message.
        :param return_address: Worker ZMQ ID.
        :param message: Heartbeat message is only the header, so unused.
        """
        with self._lock:
            if self._worker_rep is not None:
                ret_id = return_address
                if ret_id == self._worker_rep.id:
                    self._worker_rep.on_heartbeat()
                else:
                    logger.error("Received heartbeat message from unknown worker.")

    def _on_worker_disconnect(self, return_address, message):
        # type: (bytes, List[bytes]) -> None
        """
        Process worker ZMQ disconnect message.
        :param return_address: Worker ZMQ ID.
        :param message: Disconnect message is only the header, so unused.
        """
        worker_id = return_address
        self._unregister_worker(worker_id)

    def _heartbeat(self):
        # type: () -> None
        """
        This gets called periodically.  Check for dead worker and remove.
        """
        with self._lock:
            if self._worker_rep is not None:
                self._worker_rep.curr_liveness -= 1
                if not self._worker_rep.is_alive():
                    self._worker_rep = None
                    self.on_log_event("worker.unregister", "Worker disconnected.")
                else:
                    msg = [self._worker_rep.id, UNI_CLIENT_HEADER, WORKER_HEARTBEAT]
                    logger.debug("Client Sending heartbeat")
                    self._stream.send_multipart(msg)

    def _register_worker(self, worker_id):
        # type: (bytes) -> None
        """
        Register a worker and associate with a service.
        :param worker_id: The ID of the worker to register.
        """
        logger.info("_register_worker")
        if self._worker_rep is None:
            self._worker_rep = WorkerRep(worker_id)
            self._connected_event.set()
            self.on_log_event("worker.register", "Worker for '{}' is connected.".format(worker_id))
        else:
            logger.warning("Received a worker registration message when another worker is already registered.")

    def _unregister_worker(self, worker_id=None):
        # type: (bytes) -> None
        """
        Unregister a worker.
        """
        with self._lock:
            if worker_id is None or self._worker_rep is not None and worker_id == self._worker_rep.id:
                self._worker_rep = None
                self._connected_event.clear()

        self.on_log_event("worker.unregister", "Worker disconnected.")

    def _start_reply_timeout(self, timeout):
        # type: (float) -> None
        """
        Start a timer that will fire if we don't receive a ZeroMQ reply within the specified timeout.
        :param timeout: Period of time, in seconds, when timeout should happen if no reply is received.
        """
        self._timeout_handle = self._stream.io_loop.call_later(timeout, self._on_reply_timeout)

    def _stop_reply_timeout(self):
        # type: () -> None
        """
        Stop/delete the reply timeout.
        """
        if self._timeout_handle:
            self._stream.io_loop.remove_timeout(self._timeout_handle)
            self._timeout_handle = None

    @abstractmethod
    def on_message(self, msg):
        # type: (Any) -> None
        """
        This gets called when a message arrives.  It should be overloaded.

        :param msg: Any serializable datatype, or a list of serializable datatypes.
        """
        raise NotImplementedError()

    @abstractmethod
    def on_partial_message(self, msg):
        # type: (Any) -> None
        """
        This gets called if/when a worker gives a partial reply to a message.  It should be overloaded.

        :param msg: Any serializable datatype, or a list of serializable datatypes.
        """
        raise NotImplementedError()

    @abstractmethod
    def on_timeout(self):
        # type: () -> None
        """
        This gets called when a reply timeout occurs.  Override it.
        """
        raise NotImplementedError()


class WorkerRep(object):
    """
    Helper class to represent the connected worker.
    """

    def __init__(self, worker_id):
        # type: (bytes) -> None
        self.id = worker_id
        self.curr_liveness = HB_LIVENESS

    def on_heartbeat(self):
        # type: () -> None
        """
        Called when a heartbeat message from the worker was received.
        """
        if self.is_alive():
            self.curr_liveness = HB_LIVENESS
        else:
            logger.warning("Received heartbeat from dead worker")

    def is_alive(self):
        # type: () -> bool
        """
        Returns True when the worker is considered alive.
        :return: True if worker alive, otherwise false.
        """
        return self.curr_liveness > 0

