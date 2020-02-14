import logging
import traceback
from xero.uni.uniworkerthread import UniWorkerThread

try:
    from typing import Any, Dict, List, Optional, Tuple, Union
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ConsoleUniWorkerThread(UniWorkerThread):

    internal_event_time = None

    def __init__(self, endpoint, context=None):
        super(ConsoleUniWorkerThread, self).__init__(endpoint, context)

        self.methods = {
            'compare': ConsoleUniWorkerThread.compare,
            'add': ConsoleUniWorkerThread.add,
            'get_true': ConsoleUniWorkerThread.get_true,
            'set_event_time': ConsoleUniWorkerThread.set_event_time,
            'get_event_time': ConsoleUniWorkerThread.get_event_time,
            'give_get_string': ConsoleUniWorkerThread.give_get_string,
        }

    def on_log_event(self, event, message):
        # type: (str, str) -> None
        print(message)

    def do_work(self, name, args, kwargs):
        # type: (str, List[Any], Dict[Any,Any]) -> None
        try:
            try:
                #logger.debug("starting job '{}'".format(name))
                method_to_call = self.methods[name]
            except KeyError:
                method_to_call = None
            if not method_to_call:
                print("called unknown method '{}'".format(name))
                raise Exception('method {} not found'.format(name))

            self.send_reply('started', partial=True)
            result = method_to_call(*args, **kwargs)
        except BaseException as e:
            print("exception in job '{}'".format(name))
            print(traceback.format_exc())
            ex = {
                'class': type(e).__name__,
                'message': format(e),
                'traceback': traceback.format_exc()
            }
            self.send_reply(ex, exception=True)
            return

        #logger.debug("finishing job '{}'".format(name))
        self.send_reply(result)

    @staticmethod
    def compare(str1, str2):
        # type: (Any, Any) -> bool
        if str1 == str2:
            return {'equal': True}
        return {'equal': False}

    @staticmethod
    def add(val1, val2):
        # type: (Any, Any) -> Any
        return val1 + val2

    @staticmethod
    def get_true():
        # type: () -> bool
        return True

    @classmethod
    def set_event_time(cls, event_time):
        cls.internal_event_time = event_time
        return True

    @classmethod
    def get_event_time(cls):
        return cls.internal_event_time

    @classmethod
    def give_get_string(cls, str_val):
        assert type(str_val) is str
        return "returned string"

