import logging
import time
import os
from datetime import timedelta

_logger = None

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


class LogFormatter:
    def __init__(self, use_color=True):
        self.start_time = time.time()
        self.use_color = use_color

    def format(self, record):
        elapsed_seconds = round(record.created - self.start_time)

        prefix = '{} [{}] - {} - {}'.format(
            record.levelname,
            os.getpid(),
            time.strftime('%x %X'),
            timedelta(seconds=elapsed_seconds)
        )
        message = record.getMessage()
        message = message.replace('\n', '\n' + ' ' * (len(prefix) + 3))
        color = COLORS[record.levelname]
        return '\033[0;{}40m {} - {}'.format(color, prefix, message)


def get_logger(filepath=None):
    global _logger
    if _logger is not None:
        assert _logger is not None
        return _logger

    assert filepath is not None

    log_formatter = LogFormatter()

    file_handler = logging.FileHandler(filepath, 'a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)

    logger = logging.getLogger()
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    def reset_time():
        log_formatter.start_time = time.time()

    logger.reset_time = reset_time

    _logger = logger

    return logger
