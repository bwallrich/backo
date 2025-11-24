"""
Logging file
"""

import logging
import logging.handlers
import sys
import types


def get_last_message_for_a_logger(self):
    """
    return the last message by calling
    """
    for handler in self.handlers:
        if not hasattr(handler, "get_last_message"):
            continue
        c = getattr(handler, "get_last_message")
        if callable(c):
            return c()
    return None


GREY = "\x1b[38;21m"
OKGREEN = "\033[92m"
YELLOW = "\x1b[33;21m"
RED = "\033[91m"
BOLD_RED = "\033[91m\033[1m"
RESET_COLOR = "\x1b[0m"

FORMATS = {
    logging.DEBUG: logging.Formatter(
        "%(levelname)s-%(name)s-%(pathname)s.%(lineno)d : %(message)s"
    ),
    logging.INFO: logging.Formatter("%(levelname)s :%(message)s"),
    logging.WARNING: logging.Formatter("%(levelname)s : %(message)s"),
    logging.ERROR: logging.Formatter("%(levelname)s : %(message)s"),
    logging.CRITICAL: logging.Formatter("%(levelname)s : %(message)s"),
}
FORMATS_COLOR = {
    logging.DEBUG: logging.Formatter(
        OKGREEN
        + "%(levelname)s-%(name)s-%(pathname)s.%(lineno)d : %(message)s"
        + RESET_COLOR
    ),
    logging.INFO: logging.Formatter(GREY + "%(levelname)s : %(message)s" + RESET_COLOR),
    logging.WARNING: logging.Formatter(
        YELLOW + "%(levelname)s : %(message)s" + RESET_COLOR
    ),
    logging.ERROR: logging.Formatter(RED + "%(levelname)s : %(message)s" + RESET_COLOR),
    logging.CRITICAL: logging.Formatter(
        BOLD_RED + "%(levelname)s : %(message)s" + RESET_COLOR
    ),
}


class MyFormatter(logging.Formatter):
    """
    My custom format class depending on level
    """

    def __init__(self, color=False, fmt="%(levelname)s : %(message)s"):
        self.color = bool(color)
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        f = FORMATS_COLOR if self.color else FORMATS

        if record.levelno in f:
            return f[record.levelno].format(record)

        return logging.Formatter.format(self, record)


class Logger:
    """
    A logging system
    """

    def __init__(self):
        """
        Initialisation
        """
        self.loggers = {}
        self.handlers_for_all = []

    def get_or_create_logger(self, name, level=logging.ERROR):
        """
        Create a logger
        """
        if name in self.loggers:
            l = self.loggers.get(name)
        else:
            l = logging.getLogger(name)
            self.loggers[name] = l
            # Adding all previous handler
            for handler in self.handlers_for_all:
                l.addHandler(handler)

        l.setLevel(level)

        # Adding a methode to get the last message
        # use for test
        l.get_last_message = types.MethodType(get_last_message_for_a_logger, l)
        return l

    def setLevel(self, level):  # pylint: disable=invalid-name
        """
        change the level for all loggers
        """
        for logger in self.loggers.values():
            logger.setLevel(level)

    def add_handler(self, handler, name="all"):
        """
        Add an handler to a specific logger, or add
        to all handlers (by default)
        """
        if name != "all":
            l = self.loggers.get(name)
            if l is None:
                return
            l.addHandler(handler)
            return

        # For all
        self.handlers_for_all.append(handler)
        for logger in self.loggers.values():
            logger.addHandler(handler)

    def set_streamhandler(self, **kwargs):
        """
        Build an handler for stream (STDERR)
        """
        f = MyFormatter(True)
        streamhandler = logging.StreamHandler(kwargs.pop("stream", sys.stderr))
        streamhandler.setLevel(kwargs.pop("loglevel", logging.DEBUG))
        streamhandler.setFormatter(f)
        return streamhandler

    def set_filehandler(self, filename, **kwargs):
        """
        Build an handler for file
        """
        f = MyFormatter()
        filehandler = logging.FileHandler(filename)
        filehandler.setLevel(kwargs.pop("loglevel", logging.DEBUG))
        filehandler.setFormatter(f)
        return filehandler

    def set_memoryhandler(self, target, **kwargs):
        """
        Build an memory handler (only used by test)
        """
        h = logging.handlers.MemoryHandler(
            capacity=kwargs.pop("capacity", 100),
            flushLevel=kwargs.pop("flushLevel", 1000),
            target=target,
        )
        # Adding a methode to get the last message
        # use for test
        h.get_last_message = types.MethodType(
            lambda self: self.buffer[-1] if len(self.buffer) else None, h
        )
        return h


log_system = Logger()
