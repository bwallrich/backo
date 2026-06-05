# pylint: disable=unused-argument, relative-beyond-top-level
"""
Module providing the Generic() Class for file connector
"""

import uuid
import sys
from typing import Generator
from abc import ABC, abstractmethod

# used for developpement
sys.path.insert(1, "../../../stricto")

from stricto import Kparse, validation_parameters


KPARSE_MODEL = {
    "buffer_size": {"type": int, "default": 8192},
}


class FileConnector(ABC):  # pylint: disable=too-many-instance-attributes
    """
    Abstract Class fir File connector.
    this is the family (parent) object for files connector
    """

    @validation_parameters
    def __init__(self, **kwargs):
        """
        :param kwargs: arguments as kwargs for the FileConnector
        :type kwargs: object

        :keyword buffer_size: The biffer size (default = 0812)
        :type buffer_size: int
        """

        options = Kparse(kwargs, KPARSE_MODEL, strict=True)
        self._buffer_size = options.get("buffer_size")

    def generate_id(self) -> str:  # pylint: disable=unused-argument
        """
        The function to generate a random id.

        :return: an Id
        :rtype: str

        """
        return str(uuid.uuid4().int >> 64)

    @abstractmethod
    def has_file(self, file_id: str) -> bool:
        """
        check if the file exists

        :param file_id: file id
        :type file_id: str

        :return: True if the file exists
        :rtype: bool

        """

    @abstractmethod
    def clear(self, file_id: str) -> None:
        """
        Set the file given by its file_id to empty

        :param file_id: file id
        :type file_id: str
        """

    @abstractmethod
    def get(self, file_id: str, mode: str = "rb", encoding: str | None = None) -> bytes:
        """
        Return the content of the file

        :param file_id: file id
        :type file_id: str

        :return: the file content
        :rtype: bytes
        """

    @abstractmethod
    def read_chunk(self, file_id: str) -> Generator:
        """

        Read a chunk of the file

        :param file_id: file id
        :type file_id: str

        :return: a generator to get the next chunk
        :rtype: Generator

        """

    @abstractmethod
    def write_chunk(self, filename: str, chunk: bytes) -> str | None:
        """

        Append a chunk to the file

        :param file_id: file id
        :type file_id: str
        :param chunk: the chunk content
        :type chunk: bytes


        """

    @abstractmethod
    def delete(self, filename: str) -> None:
        """
        Delete the file

        :param file_id: file id
        :type file_id: str
        """
