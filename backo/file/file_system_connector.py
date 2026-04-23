# pylint: disable=consider-using-with, relative-beyond-top-level

"""
Module providing class for file in a file system
"""

import sys
import os
import tempfile
from typing import Generator

# used for developpement
sys.path.insert(1, "../../../stricto")
sys.path.insert(1, "..")

from stricto import Kparse, validation_parameters, SSyntaxError
from .file_connector import FileConnector
from ..error import FileError
from ..log import log_system, LogLevel

log = log_system.get_or_create_logger("file", LogLevel.DEBUG)


KPARSE_MODEL = {
    "path": {"type": str, "default": tempfile.gettempdir()},
}


class FileSystemConnector(
    FileConnector
):  # pylint: disable=too-many-instance-attributes

    @validation_parameters
    def __init__(self, **kwargs):
        """
        File connector on a file system

        This is the way to save / store / retrieve objects


        :param path=: The directory to store files
        :type path=: str

        """

        options = Kparse(kwargs, KPARSE_MODEL)
        self._path = options.get("path")

        if not os.path.isdir(self._path):
            raise SSyntaxError('File path "{0}" is not a directory', self._path)

        FileConnector.__init__(self, **kwargs)

    def has_file(self, file_id: str) -> bool:
        """
        check if the file exists

        :param file_id: file id
        :type file_id: str

        :return: True if the file exists
        :rtype: bool

        """
        log.debug(f"check file {os.path.join(self._path, file_id)}")
        return os.path.isfile(os.path.join(self._path, file_id))

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
        full_filename = os.path.join(self._path, file_id)

        log.debug(f"Read file {os.path.join(self._path, file_id)}")
        try:
            fd = open(full_filename, mode, encoding=encoding)
            r = fd.read()
            fd.close()
            return r
        except Exception as e:
            raise FileError("{0} read error ({1})", full_filename, repr(e)) from e

    def clear(self, file_id: str) -> None:
        """
        Set the file given by its file_id to empty

        :param file_id: file id
        :type file_id: str
        """
        full_filename = os.path.join(self._path, file_id)
        with open(full_filename, "wb"):
            pass

    def read_chunk(self, file_id: str) -> Generator:
        """
        
        Read a chunk of the file

        :param file_id: file id
        :type file_id: str

        :return: a generator to get the next chunk
        :rtype: Generator

        """
        full_filename = os.path.join(self._path, file_id)
        with open(full_filename, "rb") as fd:
            chunk = fd.read(self._buffer_size)
            while chunk:
                yield chunk
                chunk = fd.read(self._buffer_size)

        return chunk

    def write_chunk(self, file_id: str, chunk: bytes) -> None:
        """        
        
        Append a chunk to the file

        :param file_id: file id
        :type file_id: str
        :param chunk: the chunk content
        :type chunk: bytes


        """

        full_filename = os.path.join(self._path, file_id)

        try:
            fd = open(full_filename, "ab")
            fd.write(chunk)
            fd.close()
        except Exception as e:
            raise FileError(
                "{0} write chunk error ({1})", full_filename, repr(e)
            ) from e

    def delete(self, file_id: str) -> None:
        """
        Delete the file on dist

        :param file_id: file id
        :type file_id: str
        """
        full_filename = os.path.join(self._path, file_id)
        log.debug(f"Delete file {full_filename}")
        if os.path.isfile(full_filename):
            try:
                os.unlink(full_filename)
            except Exception as e:
                raise FileError("{0} delete ({1})", full_filename, repr(e)) from e
