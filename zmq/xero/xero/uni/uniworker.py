import logging
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
    from typing import Any, Dict, List, Optional, Tuple
except ImportError:
    Any = None
    List = None
    Tuple = None

logger = logging.getLogger(__name__)


class UniWorker(object):
    """
    Implementation of "simple" ZeroMQ Paranoid Pirate communication scheme.  This class is the DEALER, and performs the
    "reply" in RPC calls.  By design, only supports one remote client (ROUTER) in order to keep example simple.
    Supports a very basic RPC interface, using MessagePack for encoding/decoding.
    """

    __metaclass__ = ABCMeta

    def __init__(self, endpoint, context=None):
        # type: (str, zmq.Context) -> None
        """
        Initialize the worker.
        :param endpoint: ZeroMQ endpoint to connect to.
        :param context: ZeroMQ Context
        """
        self._context = context or zmq.Context.instance()
        self._endpoint = endpoint
        self._stream = None  # type: Optional[ZMQStream]
        self._tmo = None
        self._need_handshake = True
        self._ticker = None  # type: Optional[PeriodicCallback]
        self._delayed_cb = None
        self._connected_event = Event()
        self._lock = Lock()

        self._create_stream()

        self._curr_liveness = HB_LIVENESS
        self._keep_running = True

    def _create_stream(self):
        # type: () -> None
        """
        Helper function to create the ZMQ stream, configure callbacks.
        """
        self.on_log_event("uniworker.connect", "Trying to connect to client")
        socket = self._context.socket(zmq.DEALER)

        self._stream = ZMQStream(socket, IOLoop())
        self._stream.on_recv(self._on_message)
        self._stream.socket.setsockopt(zmq.LINGER, 0)
        self._stream.connect(self._endpoint)

        self._ticker = PeriodicCallback(self._tick, HB_INTERVAL)
        self._send_ready()
        self._ticker.start()

    def run(self):
        # type: () -> None
        """
        Start the IOLoop, a blocking call to send/recv ZMQ messsages until the IOLoop is stopped.
        Note: The name of this function needs to stay the same so UniWorkerThread's run() is overridden with this function.
        """
        if self._keep_running:
            self._stream.io_loop.start()

    def stop(self):
        # type: () -> None
        """
        Stop the IOLoop.
        """
        with self._lock:
            self._keep_running = False
            if self._stream is not None:
                self._stream.io_loop.stop()
            else:
                logger.warning("Can't stop worker-has shutdown() been called?")

    def shutdown(self):
        # type: () -> None
        """
        Close the stream/socket.  This should be called with the final flag when closing the connection for the last time.
        """

        with self._lock:
            if self._ticker:
                self._ticker.stop()
                self._ticker = None
            if not self._stream:
                return

            self._stream.on_recv(None)
            self._send_disconnect()
            self._stream.close()
            self._stream = None
            self._need_handshake = True

    def wait_for_client(self, timeout):
        # type: (float) -> None
        """
        Wait for the worker to establish a connection with the remote client.
        Will return immediately if already connected.
        Typically, the worker provides a service/responds to requests, so this is really only used for unit testing.
        :param timeout: Max time, in seconds, to wait for the connection to establish.
        """
        event_status = self._connected_event.wait(timeout)
        if not event_status:
            raise LostRemoteError("No worker is connected.")

    def is_connected(self):
        # type: () -> bool
        """
        Returns whether worker is connected to a client.
        :return: A boolean flag to indicate whether a connection to a client is established.
        """
        return not self._need_handshake

    def send_reply(self, msg, partial=False, exception=False):
        # type: (Any, bool, bool) -> None
        """
        Send a ZeroMQ message in reply to a client request.
        This should only be called out of the overridden do_work method.

        :param msg: The message to be sent out.
        :param partial: Flag indicating whether the response is a partial or final ZMQ message.
        """

        msg = msgpack.Packer(default=XeroSerializer.encoder).pack(msg)
        if exception:
            to_send = [WORKER_EXCEPTION]
        elif partial:
            to_send = [WORKER_PARTIAL_REPLY]
        else:
            to_send = [WORKER_FINAL_REPLY]
        to_send.append(b'')
        if isinstance(msg, list):
            to_send.extend(msg)
        else:
            to_send.append(msg)

        self._stream.send_multipart(to_send, track=True, copy=False)

    def emit(self, msg):
        # type: (Any) -> None
        if not self.is_connected():
            raise LostRemoteError("No client is connected.")
        msg = msgpack.Packer(default=XeroSerializer.encoder).pack(msg)
        to_send = [WORKER_EMIT]
        to_send.append(b'')
        if isinstance(msg, list):
            to_send.extend(msg)
        else:
            to_send.append(msg)
        self._stream.io_loop.add_callback(lambda x: self._stream.send_multipart(x, track=True, copy=False), to_send)

    def _tick(self):
        # type: () -> None
        """
        Periodic callback to check connectivity to client.
        """
        if self._curr_liveness >= 0:
            self._curr_liveness -= 1

        if self._curr_liveness > 0:
            self._send_heartbeat()
        elif self._curr_liveness == 0:
            # Connection died, close on our side.
            self.on_log_event("uniworker.tick", "Connection to uniclient timed out, disconnecting")
            self._connected_event.clear()
        else:
            self._send_ready()

    def _send_heartbeat(self):
        # type: () -> None
        """
        Send a heartbeat message to the client.
        """
        # Heartbeats should go out immediately, if a lot of messages to be emitted are queued up heartbeats should
        # still be sent out regularly.  Therefore, send it out via the stream's socket, rather than the stream itself
        # See https://pyzmq.readthedocs.io/en/latest/eventloop.html#send
        self._stream.send_multipart([WORKER_HEARTBEAT])

    def _send_disconnect(self):
        # type: () -> None
        """
        Send a disconnect message to the client.
        """
        # Send out via the socket, this message takes priority.
        self._stream.send_multipart([WORKER_DISCONNECT])

    def _send_ready(self):
        # type: () -> None
        """
        Send a ready message to the client.
        """
        self.on_log_event("uniworker.ready", "Sending ready to client.")
        self._stream.send_multipart([WORKER_READY])

    def _on_message(self, msg):
        # type: (List[bytes]) -> None
        """
        Processes a received ZeroMQ message.
        :param msg: List of strings in the format:
            [ ZMQ Client ID, Header, StrMessagePart1, StrMessagePart2...]
        """

        # 2nd part is protocol version
        protocol_version = msg.pop(0)
        if protocol_version != UNI_CLIENT_HEADER:  # version check, ignore old versions
            logger.error("Message doesn't start with {}".format(UNI_CLIENT_HEADER))
            return
        # 3rd part is message type
        msg_type = msg.pop(0)
        # any message resets the liveness counter
        self._need_handshake = False
        self._connected_event.set()
        self._curr_liveness = HB_LIVENESS
        if msg_type == WORKER_DISCONNECT:  # disconnect
            self._curr_liveness = 0  # reconnect will be triggered by hb timer
        elif msg_type == WORKER_REQUEST:  # request
            # remaining parts are the user message
            self._on_request(msg)
        elif msg_type == WORKER_HEARTBEAT:
            # received hardbeat - timer handled above
            pass
        else:
            logger.error("Uniworker received unrecognized message")

    def _on_request(self, message):
        # type: (List[bytes]) -> None
        """
        This gets called on incoming RPC messages, will break up the encoded message into something do_work() can process
        :param message: 
        """
        name = str(message[0], 'utf-8')
        args = msgpack.unpackb(message[1], object_hook=XeroSerializer.decoder, raw=False)
        kwargs = msgpack.unpackb(message[2], object_hook=XeroSerializer.decoder, raw=False)
        self.do_work(name, args, kwargs)

    def on_log_event(self, event, message):
        # type: (str, str) -> None
        """
        Called on internal loggable events.  Designed for override.
        :param event: The event type.
        :param message: Loggable message.
        """
        logger.debug("{}: {}".format(event, message))

    @abstractmethod
    def do_work(self, name, args, kwargs):
        # type: (str, List[Any], Dict[Any,Any]) -> None
        """
        Override this method for worker-specific message handling.
        :param name: The 'name' of the function/rpc call.
        :param args: Function call arguments.
        :param kwargs: Function call key arguments.
        """
        raise NotImplementedError()
