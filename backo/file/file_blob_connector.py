"""
Module providing the file connector in a Blob
"""

import uuid
import sys
import os
import tempfile
from typing import Generator

# used for developpement
sys.path.insert(1, "../../../stricto")
sys.path.insert(1, "..")

from stricto import Kparse, validation_parameters, SSyntaxError, Bytes
from .file_connector import FileConnector
from ..error import DBError


class FileBlobConnector(FileConnector):  # pylint: disable=too-many-instance-attributes
    """File connector Connector

    This is the way to save / store / retrieve objects

    :param ``**kwargs``:
        - *restriction=* ``func`` --
          not used yet


    """

    @validation_parameters
    def __init__(self, **kwargs):
        """Constructor"""

        # The array of bytes
        self._blobs = {}

        FileConnector.__init__(self, **kwargs)

    def has_file(self, filename: str) -> bool:
        """
        check if the file exists
        """
        return filename in self._blobs

    def raw(self, filename: str) -> Bytes:

        if filename not in self._blobs:
            self._blobs[filename] = Bytes()

        return self._blobs[filename]

    def get(self, filename: str, mode: str) -> str | bytes:
        """Return the content of the file

        :return: _description_
        :rtype: str|bytes
        """
        if filename not in self._blobs:
            return None

        b = self._blobs[filename]
        if mode == "rb":
            return b.get_value()
        if mode == "r":
            return b.get_value().decode("utf-8")

    def read_chunk(self, filename: str, buffer_size: int = 2048) -> Generator | None:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """
        bvalue = self._blobs[filename].get_value()
        if bvalue is None:
            return None

        barray = bytearray(self._blobs[filename].get_value())
        index = 0
        while index < len(barray):
            yield barray[index : index + buffer_size]
            index += buffer_size
        return barray[index : index + buffer_size]

    def write_chunk(self, filename: str, chunk: bytes) -> str:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """

        fname = self.generate_id() if filename is None else filename

        if fname not in self._blobs:
            self._blobs[fname] = Bytes(default=b"")

        barray = bytearray(self._blobs[fname].get_value())
        barray += bytearray(chunk)
        self._blobs[fname].set(bytes(barray))

        return fname

    def set(self, filename: str, mode: str, content: str | bytes) -> None:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """

        fname = self.generate_id() if filename is None else filename

        if fname not in self._blobs:
            self._blobs[fname] = Bytes()

        if mode == "wb":
            self._blobs[fname].set(content)
            return b.get_value()
        if mode == "w":
            b = bytes(content, "utf-8")
            self._blobs[fname].set(b)

        return fname

    def delete(self, filename: str) -> None:
        """Clear

        :param filename: _description_
        :type filename: str
        """
        del self._blobs[filename]
