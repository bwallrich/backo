# pylint: disable=relative-beyond-top-level, attribute-defined-outside-init
"""Module providing the File() Class"""

import copy
import inspect
import uuid
import re
import base64, binascii
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import sys
import magic


# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Kparse, Dict, String, Int, Bool, STypeError
from .file_connector import FileConnector
from ..error import FileError
from ..log import log_system, LogLevel, stack

log = log_system.get_or_create_logger("file", LogLevel.DEBUG)

MIME = magic.Magic(mime=True)

KPARSE_MODEL = {
    "encoding": {"type": str, "default": "utf-8"},
    "buffer_size": {"type": int, "default": 3},
    "buffering": int,
    "work_connector|work|connector|wc|wconnector*": {
        "type": FileConnector,
        "default": FileConnector(),
    },
    "storage_connector|storage|cold|cold_connector": FileConnector,
    "on": {"type": list[tuple], "default": []},
}

FILE_MODEL = {
    "filename": String(),
    "file_id": String(),
    "mime_type": String(),
    "encoding": String(),
    "modified": Bool(default=False),
    "buffering": Int(),
}


class File(Dict):
    """File type

    :param ``**kwargs``:
        See :py:class:`GenericType`

    :Specifics Arguments:
        * *stotrage* (``str``) --
          the directory to store the file

    """

    def __init__(self, **kwargs):
        """Constructor method"""

        log.setLevel(LogLevel.DEBUG)

        options = Kparse(kwargs, KPARSE_MODEL)

        self._work_connector: FileConnector = options.get("work_connector")
        self._storage_connector: FileConnector = options.get("storage_connector")

        self._buffers_size = options.get("buffer_size")
        encoding = options.get("encoding")
        buffering = options.get("buffering")
        self._modes = {
            "w": "wb" if encoding is None else "w",
            "r": "rb" if encoding is None else "r",
            "a": "ab" if encoding is None else "a",
        }

        on = copy.copy(options.get("on"))
        on.append(("before_save", self.on_before_save))
        on.append(("before_delete", self.on_before_delete))

        Dict.__init__(self, FILE_MODEL, on=on, **kwargs)

        # To avoid on_change trigged, modify directly values
        self.__dict__["encoding"].set(encoding)
        self.__dict__["buffering"].set(buffering)

    def __copy__(self):
        """remap copy to make a copy of the file too

        :return: _description_
        :rtype: _type_
        """
        b = super().__copy__()

        # Copy the file if exists and change file_id
        f_id = self.file_id.get_value()
        if f_id is not None:
            b.generate_file_id()
            b.copy_file_content(
                f_id, self._work_connector, b.file_id.get_value(), b._work_connector
            )
        return b

    def has_file(self) -> bool:
        f_id = self.file_id.get_value()
        if f_id is None:
            return False
        return True

    def check_type(
        self,
        value,
    ):
        if isinstance(value, FileStorage):
            return True
        if isinstance(value, bytes):
            return True
        if isinstance(value, str):
            return True
        return super().check_type(value)

    def get_content(self) -> bytes | None:
        """Get the file content

        :return: the content of the file
        :rtype: str|bytes
        """
        log.debug(
            f"{self.path_name()} file get_content() for {self.filename} {self.file_id}"
        )
        f_id = self.file_id.get_value()
        if f_id is None:
            raise FileError("{0} file doesnt exists", self.path_name())

        # Get file From storage if not there
        if not self._work_connector.has_file(f_id):
            self.load()
            if not self._work_connector.has_file(f_id):
                raise FileError(
                    '{0} file "{1}" not found in storage', self.path_name(), f_id
                )

        return self._work_connector.get(f_id)

    def generate_file_id(self) -> str:  # pylint: disable=unused-argument
        """
        The function to generate an Id.

        :param o: The object given (json format)
        :type o: dict
        :return: an Id
        :rtype: str

        """
        self.file_id.set(str(uuid.uuid4().int >> 64))
        return str(uuid.uuid4().int >> 64)

    def _set_content_from_bytes(self, content: bytes) -> None:

        log.debug(
            f"{self.path_name()} file _set_content_from_bytes() for {self.filename}"
        )
        f_id = self.file_id.get_value()
        if f_id is None:
            self.generate_file_id()
            f_id = self.file_id.get_value()

        self._work_connector.set(f_id, content)
        self.mime_type = MIME.from_buffer(content)
        self.modified = True

    def _set_content_from_str(self, content: str) -> None:

        log.debug(
            f"{self.path_name()} file _set_content_from_str() for {self.filename}"
        )
        f_id = self.file_id.get_value()
        if f_id is None:
            self.generate_file_id()
            f_id = self.file_id.get_value()

        b = content.encode("utf-8")
        self._work_connector.set(f_id, b)
        self.mime_type = MIME.from_buffer(content)
        self.modified = True

    def _set_content_from_FileStorage(self, content: FileStorage) -> None:
        """Set the content of the file from a FileStorage

        :param content: the content
        :type content: FileStorage
        :return: ( _id, mime_types )
        :rtype: tuple
        """

        log.debug(
            f"{self.path_name()} file _set_content_from_FileStorage() for {content.filename}"
        )

        f_id = self.file_id.get_value()
        if f_id is None:
            self.generate_file_id()
            f_id = self.file_id.get_value()

        chunk = content.read(self._buffers_size)

        size_read = 0
        while chunk != b"":
            size_read += len(chunk)
            self._work_connector.write_chunk(f_id, chunk)
            chunk = content.read(self._buffers_size)
        content.close()

        self.mime_type = content.mimetype
        self.modified = True
        self.filename = content.filename

    def set_content(self, content: str | bytes | FileStorage) -> None:
        """
        Set the file content
        """
        if isinstance(content, str):
            self._set_content_from_str(content)
            return

        if isinstance(content, bytes):
            self._set_content_from_bytes(content)
            return

        if isinstance(content, FileStorage):
            self._set_content_from_FileStorage(content)
            return

    def set_value_without_checks(self, value):

        # A file storage...
        if isinstance(value, FileStorage):
            self.set_content(value)
            return

        if isinstance(value, bytes):
            self.set_content(value)
            return

        # A base64 encode string ?
        if isinstance(value, str):
            match = re.match(r"^base64:(.*)", value)
            if match:
                s = match.group(1)
                try:
                    log.debug(
                        f"{self.path_name()} file set_value_without_checks() base64 value={s}"
                    )
                    self.set_content(base64.b64decode(s.encode("utf-8"), validate=True))
                except binascii.Error as e:
                    raise STypeError(
                        "{0} is not a valide base64 encoded string", self.path_name()
                    )
                return

            self.set_content(value)
            return
        super().set_value_without_checks(value)

    def delete_content(self) -> None:
        """Delete the file"""
        f_id = self.file_id.get_value()
        if f_id is not None:
            self._work_connector.delete(f_id)
        self.file_id.set(None)

    def copy_file_content(
        self, f_id_src: str, src: FileConnector, f_id_dst: str, dst: FileConnector
    ) -> str | None:
        """Copy a file from an connector to another

        :param src: _description_
        :type src: FileConnector
        :param dst: _description_
        :type dst: FileConnector
        """

        if not src.has_file(f_id_src):
            return None

        chunk_iterator = src.read_chunk(f_id_src)
        if chunk_iterator is None:
            return None

        _id = None
        for chunk in chunk_iterator:
            _id = dst.write_chunk(f_id_dst, chunk)
        return _id

    def load(self) -> None:
        """
        load from the cold storage
        """
        # No cold storage, the storage is directly used
        if self._storage_connector is None:
            return

        f_id = self.file_id.get_value()
        if f_id is None:
            return

        self._work_connector.delete(f_id)
        self.copy_file_content(
            f_id, self._storage_connector, f_id, self._work_connector
        )

        # set as not modified
        self.modified = False

    def save(self) -> None:
        """
        Save to the cold storage _storage_connector
        """
        f_id = self.file_id.get_value()
        if f_id is None:
            return

        # Nothing to save
        if self.modified.get_value() is False:
            return

        # No cold storage, the storage is directly used
        if self._storage_connector is None:
            return

        self.copy_file_content(
            f_id, self._work_connector, f_id, self._storage_connector
        )

        # set as not modified
        self.modified = False

    def on_before_save(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Try to save the file if possible
        """
        return me.save()

    def on_before_delete(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Try to save the file if possible
        """
        return me.delete_content()
