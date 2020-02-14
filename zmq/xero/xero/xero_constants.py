"""
Container file for all the protocol and timing constants.
"""

HB_INTERVAL = 1000  #: in milliseconds
INITIAL_CONNECTION_TIME_SECS = 3.2  # Want this to be longer than HB_INTERVAL

HB_LIVENESS = 3    #: HBs to miss before connection counts as dead
RPC_TIMEOUT = 5.0

# These values can by handy for development/troubleshooting:
#HB_LIVENESS = 3000    #: HBs to miss before connection counts as dead
#RPC_TIMEOUT = 1000.0

MDP_CLIENT_VERSION = b'MDPC02'
MDP_WORKER_VERSION = b'MDPW02'

UNI_CLIENT_HEADER = b'client'
UNI_WORKER_HEADER = b'worker'

WORKER_READY = b'\x01'  # Worker -> Broker
WORKER_REQUEST = b'\x02'  # Broker -> Worker
WORKER_PARTIAL_REPLY = b'\x03'  # Worker -> Broker
WORKER_FINAL_REPLY = b'\x04'  # Worker -> Broker
WORKER_EMIT = b'\x05'  # Worker -> Broker
WORKER_HEARTBEAT = b'\x06'  # Worker -> Broker
WORKER_DISCONNECT = b'\x07'  # Worker -> Broker
WORKER_MULTICAST_ADD = b'\x08'  # Worker -> Broker
WORKER_EXCEPTION = b'\x09'  # Worker -> Broker
WORKER_ERROR = b'\x0a'  # Worker -> Broker

CLIENT_PARTIAL_REPLY = b'\x02'  # Broker -> Client
CLIENT_FINAL_REPLY = b'\x03'  # Broker -> Client
CLIENT_ERROR = b'\x04'  # Broker -> Client
CLIENT_MULTICAST_START = b'\x05'  # Broker -> Client
CLIENT_EXCEPTION = b'\x06'  # Broker -> Client
