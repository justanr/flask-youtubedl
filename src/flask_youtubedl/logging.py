import logging


class ExcludeErrorLogFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < 40
