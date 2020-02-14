from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

try:
    from typing import Any, Dict
except ImportError:
    Any = None


class XeroSerializer(object):
    """
    MessagePack can internally handle encoding/decoding all the basic datatypes, but we need to provide it a dedicated
    encoder for any application-level objects, and some basic classes.  This class is a container for custom
    encooders/decoders
    """

    @staticmethod
    def encoder(obj):
        # type: (Any) -> Any
        """
        A messagepack-compatible encoder that can encode datetimes and timedeltas
        :param obj Any object that potentially needs to be encoded.  Typically a
        :return:
        """

        if isinstance(obj, datetime):
            return {
                '__type__': 'datetime',
                'year': obj.year,
                'month': obj.month,
                'day': obj.day,
                'hour': obj.hour,
                'minute': obj.minute,
                'second': obj.second,
                'microsecond': obj.microsecond,
            }

        elif isinstance(obj, timedelta):
            return {
                '__type__': 'timedelta',
                'days': obj.days,
                'seconds': obj.seconds,
                'microseconds': obj.microseconds,
            }

        elif isinstance(obj, Exception):
            return {
                '__type__': 'exception',
                'message': format(obj),
                'traceback': str(obj)
            }

        else:
            logger.warning("XeroSerializer doesn't how to encode object type {}".format(type(obj)))

        return obj

    @staticmethod
    def decoder(d):
        # type: (Dict) -> Any
        if '__type__' not in d:
            return d

        obj_type = d.pop('__type__')

        if obj_type == 'datetime':
            dateobj = datetime(**d)
            return dateobj
        elif obj_type == 'timedelta':
            timedeltaobj = timedelta(**d)
            return timedeltaobj
        elif obj_type == 'exception':
            exception = Exception(d.get('traceback'))
            return exception
        else:
            raise RuntimeError("XeroSerializer doesn't know how to decode {}".format(d))
