# pylint: disable=relative-beyond-top-level, attribute-defined-outside-init
"""Module providing the File() Class"""

import copy
import uuid
from typing import Any
import re
import base64
import binascii
import sys
import io
import magic
from werkzeug.datastructures import FileStorage


# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Kparse, Dict, String, Int, Bool, STypeError, SConstraintError
from .file_connector import FileConnector

from ..error import FileError
from ..log import log_system, LogLevel, stack

log = log_system.get_or_create_logger("file", LogLevel.DEBUG)

MIME = magic.Magic(mime=True)

FILE_MODEL = {
    "filename": String(),
    "file_id": String(),
    "content_type": String(),
    "size": Int(default=0),
    "modified": Bool(default=False),
}


def transform_to_filestorage(  # pylint: disable=unused-argument
    v: Any, o: Any
) -> FileStorage | None:
    """Transform any kind of object into a FileStorage

    :param v: the input object
    :type v: Any
    :return: a FileStorage "view" of this object
    :rtype: FileStorage
    """
    if v is None:
        print("transform None")
        return None

    if isinstance(v, File):
        return v

    if isinstance(v, str):
        mystring = v
        match = re.match(r"^base64:(.*)", v)
        if match:
            s = match.group(1)
            try:
                data = base64.b64decode(s.encode("utf-8"), validate=True)
            except binascii.Error as e:
                raise STypeError(
                    '"{0}" is not a valide base64 encoded string', v
                ) from e
        else:
            data = mystring.encode("utf-8")
        return FileStorage(
            stream=io.BytesIO(data),
            filename=None,
            content_type=MIME.from_buffer(data),
            content_length=len(data),
        )

    if isinstance(v, bytearray):
        b = bytes(v)
        return FileStorage(
            stream=io.BytesIO(b),
            filename=None,
            content_type=MIME.from_buffer(b),
            content_length=len(b),
        )

    if isinstance(v, bytes):
        return FileStorage(
            stream=io.BytesIO(v),
            filename=None,
            content_type=MIME.from_buffer(v),
            content_length=len(v),
        )

    return v


KPARSE_MODEL = {
    "buffer_size": {"type": int, "default": 3},
    "mime_types|content_type": list[str],
    "max_size|max": int,
    "work_connector|work|connector|wc|wconnector*": {
        "type": FileConnector,
        "default": FileConnector(),
    },
    "storage_connector|storage|cold|cold_connector": FileConnector,
    "on": {"type": list[tuple], "default": []},
}


class File(Dict):

    def __init__(self, **kwargs):
        """
        Object to manage files.
        inherite from https://stricto.readthedocs.io/en/latest/api_reference.html#stricto.Dict


        :param buffer_size=: The buffer size to read chunk on this file
        :type buffer_size=: int
        :param work_connector=: The connector for storing files
        :type work_connector=: FileConnector
        :param storage_connector=: The connector for storing files after a save() if needed.
        :type storage_connector=: FileConnector

        :param max_size=: The maximum file size autorized
        :type max_size=: int
        :param mime_types=: The list of available mime_types
        :type mime_types=: list [ str ]
              
        """

        log.setLevel(LogLevel.DEBUG)

        options = Kparse(kwargs, KPARSE_MODEL)

        self._work_connector: FileConnector = options.get("work_connector")
        self._storage_connector: FileConnector = options.get("storage_connector")

        self._buffers_size = options.get("buffer_size")

        self._authorized_mime_types = options.get("mime_types")
        self._max_size = options.get("max_size")

        on = copy.copy(options.get("on"))
        on.append(("before_save", self.on_before_save))
        on.append(("before_delete", self.on_before_delete))

        kwargs["transform"] = transform_to_filestorage

        Dict.__init__(self, FILE_MODEL, on=on, **kwargs)

        # To avoid on_change trigged, modify directly values

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
        """
        Check if the file exists / is set. (means it has a file_id)


        :return: True if OK
        :rtype: bool
        """
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
        return super().check_type(value)

    def get_content(self) -> bytes | None:
        """Get the file content

        :return: the content of the file
        :rtype: str|bytes
        """
        log.debug(
            f"{self.path_name()} file get_content() for {self.filename} {self.file_id} {stack()}"
        )
        f_id = self.file_id.get_value()
        if f_id is None:
            raise FileError("{0} file doesnt exists (no file_id)", self.path_name())

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

    def _set_content_from_filestorage(self, content: FileStorage | None) -> None:
        """Set the content of the file from a FileStorage

        :param content: the content
        :type content: FileStorage
        :return: ( _id, mime_types )
        :rtype: tuple
        """

        if content is None:
            self.set(None)
            return

        log.debug(f"{self.path_name()} file set_content()")

        f_id = self.file_id.get_value()
        if f_id is None:
            self.generate_file_id()
            f_id = self.file_id.get_value()

        chunk = content.read(self._buffers_size)

        self._work_connector.clear(f_id)

        size_read = 0
        while chunk != b"":
            size_read += len(chunk)
            self._work_connector.write_chunk(f_id, chunk)
            chunk = content.read(self._buffers_size)
        content.close()

        self.content_type = content.mimetype
        self.modified.set(True)
        if content.filename is not None:
            self.filename.set(content.filename)
        self.size.set(size_read)

    def set_content(self, content: str | bytes | FileStorage) -> None:
        """
        Set the file content
        """
        return self._set_content_from_filestorage(
            transform_to_filestorage(content, None)
        )

    def set_value_without_checks(self, value):

        if isinstance(value, (FileStorage, str, bytes)):
            self.set_content(value)
            return
        super().set_value_without_checks(value)
        return

    def delete_content(self) -> None:
        """Delete the file"""
        f_id = self.file_id.get_value()
        if f_id is not None:
            self._work_connector.delete(f_id)
        self.file_id.set(None)
        self.size.set(0)

    def copy_file_content(
        self, f_id_src: str, src: FileConnector, f_id_dst: str, dst: FileConnector
    ) -> None:
        """Copy a file from an connector to another

        :param f_id_src: The source file_id
        :type f_id_src: str
        :param src: The source FileConnector
        :type src: FileConnector
        :param f_id_dst: The destination file_id
        :type f_id_dst: str
        :param dst: The destination FileConnector
        :type dst: FileConnector
        """

        if not src.has_file(f_id_src):
            return None

        chunk_iterator = src.read_chunk(f_id_src)
        if chunk_iterator is None:
            return None

        for chunk in chunk_iterator:
            dst.write_chunk(f_id_dst, chunk)
        return None

    def load(self) -> None:
        """
        load from the cold storage

        the cold storage must exists (params storage= in initialisation)
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
        self.modified.set(False)

    def save(self) -> None:
        """
        Save to the cold storage

        the cold storage must exists (params storage= in initialisation)
        This is called by save() from `:py:class:Item` *before save* the Item itself.

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
        self.modified.set(False)

    def on_before_save(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Trigg by the event "before_save"

        """
        return me.save()

    def on_before_delete(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Try to the event "before_delete"
        """
        return me.delete_content()

    def check_constraints(self, value):

        Dict.check_constraints(self, value)  # pylint: disable=duplicate-code

        # check the max size
        if self._max_size is not None:
            size = None

            if isinstance(value, File):
                size = value.size.get_value()
            if isinstance(value, FileStorage):
                size = value.content_length

            if size is not None and size > self._max_size:
                raise SConstraintError(
                    '{0}: File too big (value="{value}")',
                    self.path_name(),
                    value=value,
                )

        # check the content_type
        if self._authorized_mime_types is not None:
            mt = None
            if isinstance(value, File):
                mt = value.content_type.get_value()
            if isinstance(value, FileStorage):
                mt = value.content_type

            if mt not in self._authorized_mime_types:
                raise SConstraintError(
                    '{0}: Unauthorized content_type (value="{mt}")',
                    self.path_name(),
                    mt=mt,
                )
        return True
