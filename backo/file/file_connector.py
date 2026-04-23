# pylint: disable=unused-argument, relative-beyond-top-level
"""
Module providing the Generic() Class for file connector
"""

import uuid
import sys
from typing import Generator

# used for developpement
sys.path.insert(1, "../../../stricto")

from stricto import Kparse, validation_parameters


KPARSE_MODEL = {
    "buffer_size": {"type": int, "default": 3},
}


class FileConnector:  # pylint: disable=too-many-instance-attributes

    @validation_parameters
    def __init__(self, **kwargs):
        """
        File connector main object.

        this is the family (parent) object for files connector
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

    def has_file(self, file_id: str) -> bool:
        """
        check if the file exists

        :param file_id: file id
        :type file_id: str

        :return: True if the file exists
        :rtype: bool

        """
        return False


    def clear(self, file_id: str) -> None:
        """
        Set the file given by its file_id to empty

        :param file_id: file id
        :type file_id: str
        """

    def get(
        self, file_id: str, mode: str = "rb", encoding: str | None = None
    ) -> bytes :
        """
        Return the content of the file

        :param file_id: file id
        :type file_id: str

        :return: the file content
        :rtype: bytes
        """
        return None

    def read_chunk(self, file_id: str) -> Generator:
        """
        
        Read a chunk of the file

        :param file_id: file id
        :type file_id: str

        :return: a generator to get the next chunk
        :rtype: Generator

        """
        return None

    def write_chunk(self, filename: str, chunk: bytes) -> str | None:
        """        
        
        Append a chunk to the file

        :param file_id: file id
        :type file_id: str
        :param chunk: the chunk content
        :type chunk: bytes


        """
        return None

    def delete(self, filename: str) -> None:
        """
        Delete the file

        :param file_id: file id
        :type file_id: str
        """
        return
