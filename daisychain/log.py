import logging
from daisychain.constants import DAISY_ROOT_LOG_ID

DEFAULT_CONSOLE_FORMATTER = logging.Formatter(('%(asctime)s:' + logging.BASIC_FORMAT).replace(':', ' : '))


def get_logger(stream):
    return logging.getLogger(DAISY_ROOT_LOG_ID + '.' + stream)


class SharedLoggingObject(object):
    log_streams = dict()

    def __init__(self, root_log_id=None):
        self.root_log_id = root_log_id

    def log(self, stream=None):
        stream_pieces = [r for r in [self.root_log_id, stream] if r is not None]
        if hasattr(self, 'name'):
            stream_pieces.append(self.name)
        log_stream = '.'.join(stream_pieces).strip('.')
        return get_logger(log_stream)
