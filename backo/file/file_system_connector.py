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

KPARSE_MODEL = {
    "path": {"type": str, "default": tempfile.gettempdir()},
}


class FileSystemConnector(
    FileConnector
):  # pylint: disable=too-many-instance-attributes
    """File connector Connector

    This is the way to save / store / retrieve objects

    :param ``**kwargs``:
        - *restriction=* ``func`` --
          not used yet


    """

    @validation_parameters
    def __init__(self, **kwargs):
        """Constructor"""

        options = Kparse(kwargs, KPARSE_MODEL)
        self._path = options.get("path")

        if not os.path.isdir(self._path):
            raise SSyntaxError('File path "{0}" is not a directory', self._path)

        FileConnector.__init__(self, **kwargs)

    def has_file(self, filename: str) -> bool:
        """
        check if the file exists
        """
        return os.path.isfile(os.path.join(self._path, filename))

    def get(self, filename: str, mode: str, encoding:str|None = None ) -> str | bytes:
        """Return the content of the file

        :return: _description_
        :rtype: str|bytes
        """
        full_filename = os.path.join(self._path, filename)

        try:
            fd = open(full_filename, mode, encoding=encoding)
            r = fd.read()
            fd.close()
            return r
        except Exception as e:
            raise FileError("{0} read error ({1})", full_filename, repr(e)) from e

    def read_chunk(self, filename: str, buffer_size: int = 2048) -> Generator:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """
        full_filename = os.path.join(self._path, filename)
        with open(full_filename, "rb") as fd:
            chunk = fd.read(buffer_size)
            while chunk:
                yield chunk
                chunk = fd.read(buffer_size)

        return chunk

    def write_chunk(self, filename: str, chunk: bytes) -> str | None:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """

        fname = self.generate_id() if filename is None else filename

        full_filename = os.path.join(self._path, fname)

        try:
            fd = open(full_filename, "ab")
            fd.write(chunk)
            fd.close()
        except Exception as e:
            raise FileError(
                "{0} write chunk error ({1})", full_filename, repr(e)
            ) from e

        return fname

    def set(self, filename: str, mode: str, content: str | bytes, encoding:str|None = None) -> str:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """
        fname = self.generate_id() if filename is None else filename

        full_filename = os.path.join(self._path, fname)

        try:
            fd = open(full_filename, mode, encoding=encoding)
            fd.write(content)
            fd.close()
        except Exception as e:
            raise FileError(
                "{0} write chunk error ({1})", full_filename, repr(e)
            ) from e

        return fname

    def delete(self, filename: str) -> None:
        """Clear

        :param filename: _description_
        :type filename: str
        """
        full_filename = os.path.join(self._path, filename)
        if os.path.isfile(full_filename):
            try:
                os.unlink(full_filename)
            except Exception as e:
                raise FileError("{0} delete ({1})", full_filename, repr(e)) from e
