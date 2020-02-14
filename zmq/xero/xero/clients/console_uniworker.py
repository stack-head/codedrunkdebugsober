import logging
import traceback

from xero.uni.uniworker import UniWorker

logger = logging.getLogger(__name__)


class ConsoleUniWorker(UniWorker):

    def __init__(self, endpoint, context=None):
        super(ConsoleUniWorker, self).__init__(endpoint, context)

        self._methods = {
            'red': self.red,
            'compare': self.compare,
        }

    def on_log_event(self, event, message):
        print(message)

    def do_work(self, name, args, kwargs):

        try:
            if name in self._methods:
                self.send_reply('started', partial=True)
                result = self._methods[name](*args, **kwargs)
                self.send_reply(result)
            else:
                print("called unknown method '{}'".format(name))
                raise Exception('method {} not found'.format(name))

        except BaseException as e:
            logger.warn("exception in job '{}'".format(name))
            logger.warn(traceback.format_exc())
            ex = {
                'class': type(e).__name__,
                'message': format(e),
                'traceback': traceback.format_exc()
            }
            self.send_reply(ex, exception=True)
            return

    @classmethod
    def red(cls):
        return "reddish"

    @classmethod
    def compare(cls, str1, str2):
        if str1 == str2:
            return [True, 1]
        return [False, 2]
