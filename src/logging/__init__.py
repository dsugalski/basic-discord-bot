import logging
import os
import sys

from logging.handlers import TimedRotatingFileHandler

# No exception handler -- not having a logging directory and not being
# able to create one is a fatal error.
os.makedirs("./logs", exist_ok=True)

formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(funcName)s(): %(message)s')

_log_stdout = logging.StreamHandler(sys.stdout)
_log_stdout.setLevel(logging.DEBUG)
_log_stdout.setFormatter(formatter)

_log_debug = TimedRotatingFileHandler(filename='logs/debug-level.log',
                                       when='W0', encoding='utf-8',
                                       backupCount=5, utc=True)
_log_debug.setLevel(logging.DEBUG)
_log_debug.setFormatter(formatter)

_log_info = TimedRotatingFileHandler(filename='logs/info-level.log',
                                     when='W0', encoding='utf-8',
                                     backupCount=5, utc=True)
_log_info.setLevel(logging.INFO)
_log_info.setFormatter(formatter)

_log_warning = TimedRotatingFileHandler(filename='logs/warning-level.log',
                                         when='W0', encoding='utf-8',
                                         backupCount=5, utc=True)
_log_warning.setLevel(logging.WARNING)
_log_warning.setFormatter(formatter)

_log_error = TimedRotatingFileHandler(filename='logs/error-level.log',
                                         when='W0', encoding='utf-8',
                                         backupCount=5, utc=True)
_log_error.setLevel(logging.ERROR)
_log_error.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Attach our log sinks to the logger object
logger.addHandler(_log_stdout)
logger.addHandler(_log_debug)
logger.addHandler(_log_info)
logger.addHandler(_log_warning)
logger.addHandler(_log_error)

logger.propagate = False
