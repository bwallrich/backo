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

    def has_file(self, file_id: str) -> bool:
        """
        check if the file exists
        """
        return file_id in self._blobs

    def get(
        self, file_id: str, mode: str = "rb", encoding: str | None = None
    ) -> bytes | str:
        """Return the content of the file

        :return: _description_
        :rtype: str|bytes
        """
        if file_id not in self._blobs:
            return None

        b = self._blobs[file_id]
        if mode == "rb":
            return b.get_value()
        if mode == "r":
            return b.get_value().decode("utf-8")

        # unknown mode
        return None

    def read_chunk(self, file_id: str) -> Generator:
        """Set the file content

        :param file_id: _description_
        :type file_id: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
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
        """Set the file content

        :param file_id: _description_
        :type file_id: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """

        if file_id not in self._blobs:
            self._blobs[file_id] = Bytes(default=b"")

        barray = bytearray(self._blobs[file_id].get_value())
        barray += bytearray(chunk)
        self._blobs[file_id].set(bytes(barray))

    def set(
        self,
        file_id: str,
        content: str | bytes,
        mode: str = "wb",
        encoding: str | None = None,
    ) -> None:
        """Set the file content

        :param file_id: _description_
        :type file_id: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """

        fname = self.generate_id() if file_id is None else file_id

        if fname not in self._blobs:
            self._blobs[fname] = Bytes()

        if mode == "wb":
            self._blobs[fname].set(content)
        if mode == "w":
            b = bytes(content, "utf-8") if isinstance(content, str) else content
            self._blobs[fname].set(b)

        return fname

    def delete(self, file_id: str) -> None:
        """Clear

        :param file_id: _description_
        :type file_id: str
        """
        if file_id in self._blobs:
            del self._blobs[file_id]
