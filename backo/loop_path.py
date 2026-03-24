"""
Loop path manipulation
"""

import logging
from .error import Error, ErrorType

DEFAULT_MAX_LOOP = 40

from .log import log_system

log = log_system.get_or_create_logger("loop", logging.INFO)


class LoopPath:
    """
    A loop object to detect loop maniipulation in reference
    """

    def __init__(self, max_loop=DEFAULT_MAX_LOOP):
        """ """
        self._path = []
        self.max_loop = max_loop

    def is_loop(self, collection_name: str, id: str, path: str) -> bool:
        """detect if already in the path

        :param collection_name: the name of the collection
        :type collection_name: str
        :param id: the id of the object in the collection
        :type id: str
        :param path: the path (ex : $.site )
        :type path: str
        :return: True if seen
        :rtype: bool
        """
        for m_path in self._path:
            if m_path == (collection_name, id, path):
                return True
        return False

    def append(self, collection_name: str, id: str, path: str) -> None:
        """Append to the path a tuple (collection, id, path )

        :param collection_name: the name of the collection
        :type collection_name: str
        :param id: the id of the object in the collection
        :type id: str
        :param path: the path (ex : $.site )
        :type path: str
        """

        if len(self._path) > self.max_loop:
            raise Error(
                ErrorType.MAX_LOOP,
                f"Loop max detected for ( {collection_name}, {id}, {path})",
            )

        self._path.append((collection_name, id, path))
