# pylint: disable=consider-using-with, relative-beyond-top-level
"""
Module providing the file connector in a Blob
"""

import sys
from typing import Generator

# used for developpement
sys.path.insert(1, "../../../stricto")

from stricto import validation_parameters, Bytes
from .file_connector import FileConnector
from ..log import log_system, LogLevel

log = log_system.get_or_create_logger("file", LogLevel.DEBUG)


class FileBlobConnector(FileConnector):  # pylint: disable=too-many-instance-attributes

    @validation_parameters
    def __init__(self, **kwargs):
        """
        File connector in memory

        This is the way to save files just in memory.


        """

        # The array of bytes
        self._blobs = {}

        FileConnector.__init__(self, **kwargs)

    def has_file(self, file_id: str) -> bool:
        """
        check if the file exists

        :param file_id: file id
        :type file_id: str

        :return: True if the file exists
        :rtype: bool

        """
        return file_id in self._blobs

    def get(
        self, file_id: str, mode: str = "rb", encoding: str | None = None
    ) -> bytes | str:
        """
        Return the content of the file

        :param file_id: file id
        :type file_id: str

        :return: the file content
        :rtype: bytes
        """
        if file_id not in self._blobs:
            return None

        b = self._blobs[file_id]
        if mode == "rb":
            return b.get_value()
        if mode == "r":
            return b.get_value().decode(encoding)

        # unknown mode
        return None

    def clear(self, file_id: str) -> None:
        """
        Set the file given by its file_id to empty

        :param file_id: file id
        :type file_id: str
        """
        if file_id in self._blobs:
            self._blobs[file_id].set(b"")

    def read_chunk(self, file_id: str) -> Generator:
        """
        
        Read a chunk of the file

        :param file_id: file id
        :type file_id: str

        :return: a generator to get the next chunk
        :rtype: Generator

        """
        bvalue = self._blobs[file_id].get_value()
        if bvalue is None:
            return None

        barray = bytearray(self._blobs[file_id].get_value())
        index = 0
        while index < len(barray):
            yield barray[index : index + self._buffer_size]
            index += self._buffer_size
        return barray[index : index + self._buffer_size]

    def write_chunk(self, file_id: str, chunk: bytes) -> None:
        """        
        
        Append a chunk to the file

        :param file_id: file id
        :type file_id: str
        :param chunk: the chunk content
        :type chunk: bytes


        """

        if file_id not in self._blobs:
            self._blobs[file_id] = Bytes(default=b"")

        barray = bytearray(self._blobs[file_id].get_value())
        barray += bytearray(chunk)
        self._blobs[file_id].set(bytes(barray))

    def delete(self, file_id: str) -> None:
        """Clear

        :param file_id: _description_
        :type file_id: str
        """
        if file_id in self._blobs:
            del self._blobs[file_id]
