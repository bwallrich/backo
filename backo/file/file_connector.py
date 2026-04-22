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
    "encoding": {"type": str, "default": "utf-8"},
    "buffering": int,
}


class FileConnector:  # pylint: disable=too-many-instance-attributes
    """File connector Connector

    This is the way to save / store / retrieve objects

    :param ``**kwargs``:
        - *restriction=* ``func`` --
          not used yet


    """

    @validation_parameters
    def __init__(self, **kwargs):
        """Constructor"""

        options = Kparse(kwargs, KPARSE_MODEL, strict=True)
        self._buffer_size = options.get("buffer_size")
        self._encoding = options.get("encoding")
        self._buffering = options.get("buffering")
        self._modes = {
            "w": "wb" if self._encoding is None else "w",
            "r": "rb" if self._encoding is None else "r",
            "a": "ab" if self._encoding is None else "a",
        }

    def generate_id(self) -> str:  # pylint: disable=unused-argument
        """
        The function to generate an Id.

        :param o: The object given (json format)
        :type o: dict
        :return: an Id
        :rtype: str

        """
        return str(uuid.uuid4().int >> 64)

    def get(self, filename: str, mode: str) -> str | bytes:
        """Return the content of the file

        MUST BE OVERWRITTEN

        :return: the file content
        :rtype: str|bytes
        """
        return None

    def set(self, filename: str, mode: str, content: str | bytes) -> str | None:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """
        return None

    def read_chunk(self, filename: str, buffer_size: int = 2048) -> Generator:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """
        return None

    def write_chunk(self, filename: str, chunk: bytes) -> str | None:
        """Set the file content

        :param filename: _description_
        :type filename: str
        :param mode: _description_
        :type mode: str
        :param content: _description_
        :type content: str | bytes
        """
        return None

    def delete(self, filename: str) -> None:
        """Delete the file

        :param filename: _description_
        :type filename: str
        """
        return
