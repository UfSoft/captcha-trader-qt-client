# -*- coding: utf-8 -*-
"""
    ST-Log
    ~~~~~~

    Simple package that extends python's standard logging by adding to it
    two(2) additional levels, lower than `DEBUG`, `TRACE` and `GARBAGE`.

    Also helps setting up a console and/or a logfile handler(s).

    :copyright: © 2011 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

__version__         = '0.9'
__package_name__    = 'ST-Log'
__summary__         = "Python's standard logging helpers"
__author__          = 'Pedro Algarvio'
__email__           = 'pedro@algarvio.me'
__license__         = 'BSD'
__url__             = 'http://dev.ufsoft.org/projects/log'
__description__     = __doc__

import new
import logging

logging.TRACE = 5
logging.GARBAGE = 1

LOG_LEVELS = {
    "none": logging.NOTSET,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "none": logging.CRITICAL,
    "debug": logging.DEBUG,
    "trace": logging.TRACE,
    "garbage": logging.GARBAGE
}

LoggingLoggerClass = logging.getLoggerClass()

DEFAULT_FMT = '%%(asctime)s,%%(msecs)03.0f [%%(name)-%ds:%%(lineno)-4s][%%(levelname)-8s] %%(message)s'
MAX_LOGGER_NAME_LENGTH = 5


class Logging(LoggingLoggerClass):
    def __new__(cls, logger_name, *args, **kwargs):
        global MAX_LOGGER_NAME_LENGTH
        # This makes module name padding increase to the biggest module name
        # so that logs keep readability.
        instance = super(Logging, cls).__new__(cls)
        if len(logger_name) > MAX_LOGGER_NAME_LENGTH:
            MAX_LOGGER_NAME_LENGTH = len(logger_name)
            formatter = logging.Formatter(DEFAULT_FMT % MAX_LOGGER_NAME_LENGTH,
                                          datefmt="%H:%M:%S")
            for handler in logging.getLogger().handlers:
                if not handler.lock:
                    handler.createLock()
                handler.acquire()
                handler.setFormatter(formatter)
                handler.release()
        return instance

def setup_logging(increase_padding=False):
    """
    Setup overall logging engine and add 2 more levels of logging lower than
    DEBUG, TRACE and GARBAGE.
    """
    import logging

    if increase_padding and logging.getLoggerClass() is not Logging:
        logging.setLoggerClass(Logging)

    if not hasattr(LoggingLoggerClass, 'trace'):
        def trace(cls, msg, *args, **kwargs):
            return cls.log(5, msg, *args, **kwargs)

        logging.addLevelName(5, 'TRACE')
        LoggingLoggerClass.trace = new.instancemethod(
            trace, None, LoggingLoggerClass
        )

    if not hasattr(LoggingLoggerClass, 'garbage'):
        def garbage(cls, msg, *args, **kwargs):
            return cls.log(1, msg, *args, **kwargs)

        logging.addLevelName(1, 'GARBAGE')
        LoggingLoggerClass.garbage = new.instancemethod(
            garbage, None, LoggingLoggerClass
        )

    # Set the root logger at the lowest level possible
    logging.getLogger().setLevel(1)


def setup_console_logger(level, fmt=None, increase_padding=False):
    """
    Setup console logging.
    """
    import logging
    setup_logging(increase_padding)
    level = LOG_LEVELS.get(level.lower(), logging.ERROR)
    rootLogger = logging.getLogger()
    handler = logging.StreamHandler()

    if fmt is None:
        fmt = DEFAULT_FMT % MAX_LOGGER_NAME_LENGTH

    handler.setLevel(level)
    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    rootLogger.addHandler(handler)


def setup_logfile_logger(level, logfile, fmt=None, increase_padding=False):
    """
    Setup logfile logging.
    """
    import logging
    setup_logging(increase_padding)
    level = LOG_LEVELS.get(level.lower(), logging.ERROR)
    rootLogger = logging.getLogger()

    import logging.handlers

    # Weekly rotating log (Rotates at monday..)
    handler = logging.handlers.TimedRotatingFileHandler(
        logfile, when='w0', interval=1, backupCount=4, encoding='utf8', utc=True
    )

    if fmt is None:
        fmt = DEFAULT_FMT % MAX_LOGGER_NAME_LENGTH

    handler.setLevel(level)
    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")

    handler.setFormatter(formatter)
    rootLogger.addHandler(handler)


def set_logger_level(logger_name, level):
    """
    Tweak a specific logger's logging level
    """
    import logging
    setup_logging()
    logging.getLogger(logger_name).setLevel(
        LOG_LEVELS.get(level.lower(), logging.ERROR)
    )
