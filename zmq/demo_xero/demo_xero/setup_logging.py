import logging
import logging.config

_LOGGING_FORMAT = '%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s [%(threadName)-12s] %(message)s'
_LOGGING_DATEFMT = '%H:%M:%S'


def configure_logging(use_colored_logs=True):
    """
    We're running a command line in the program alongside normal logging.  Don't have time to do curses
    or anything fancy, so we're just going to output logs to a file and use tmux to open up a term to watch it.
    """

    logging.getLogger().setLevel(logging.DEBUG)

    if use_colored_logs:
        import coloredlogs
        coloredlogs.install(level='DEBUG',
                            fmt=_LOGGING_FORMAT,
                            datefmt=_LOGGING_DATEFMT)
    else:
        formatter = logging.Formatter(_LOGGING_FORMAT,
                                      datefmt=_LOGGING_DATEFMT)

        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)

