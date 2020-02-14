from datetime import datetime, timedelta
import msgpack
import logging
import unittest
from munch import Munch

from xero.util.xero_serialization import XeroSerializer

logger = logging.getLogger(__name__)


class TestXeroSerializer(unittest.TestCase):

    @staticmethod
    def test_xero_serializer():

        useful_integer = 5

        useful_datetime_dict = {
            "id": 1,
            "created": get_datetime_now(),
        }

        useful_timedelta_dict = {
            "id": 1,
            "created": timedelta(days=55, hours=20, minutes=35, seconds=20, milliseconds=50),
        }

        # XeroSerializer isn't needed to serialize/deserialize basic types-in fact, XeroSerializer won't even be called.
        # Just make sure it works correctly
        packed_integer = msgpack.packb(useful_integer, default=XeroSerializer.encoder)
        rebuilt_integer = msgpack.unpackb(packed_integer, object_hook=XeroSerializer.decoder, raw=False)
        assert rebuilt_integer == useful_integer

        packed_datetime_dict = msgpack.packb(useful_datetime_dict, default=XeroSerializer.encoder)
        rebuilt_datetime_dict = msgpack.unpackb(packed_datetime_dict, object_hook=XeroSerializer.decoder, raw=False)
        assert rebuilt_datetime_dict == useful_datetime_dict

        packed_timedelta_dict = msgpack.packb(useful_timedelta_dict, default=XeroSerializer.encoder)
        rebuilt_timedelta_dict = msgpack.unpackb(packed_timedelta_dict, object_hook=XeroSerializer.decoder, raw=False)
        assert rebuilt_timedelta_dict == useful_timedelta_dict

        simple_munch = Munch(name='foo', type='bar', date=datetime.now())
        packed_munch = msgpack.packb(simple_munch, default=XeroSerializer.encoder)
        rebuilt_munch = msgpack.unpackb(packed_munch, object_hook=XeroSerializer.decoder, raw=False)
        assert rebuilt_munch == simple_munch

        simple_string = 'this_should_be_string'
        packed_string = msgpack.packb(simple_string, default=XeroSerializer.encoder)
        rebuilt_string = msgpack.unpackb(packed_string, object_hook=XeroSerializer.decoder, raw=False)
        assert type(rebuilt_string) is str
        assert rebuilt_string == simple_string

#        unicode_string = u'this_should_be_unicode'
#        packed_unicode_string = msgpack.packb(unicode_string, default=XeroSerializer.encoder)
#        rebuilt_unicode_string = msgpack.unpackb(packed_unicode_string, object_hook=XeroSerializer.decoder, raw=False)
#        assert type(rebuilt_unicode_string) is str
#        assert rebuilt_unicode_string == unicode_string


def get_datetime_now():
    # type: () -> datetime
    """
    We so routinely need to get 'now' that I'm just gonna make a common function for anyone to use.
    :return: A datetime of 'now' in UTC.
    """
    return datetime.utcnow().replace(tzinfo=None)