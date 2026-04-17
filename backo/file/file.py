# pylint: disable=relative-beyond-top-level, attribute-defined-outside-init
"""Module providing the File() Class"""

import copy
import sys
import magic


# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Kparse, Dict, String, Int, Bool
from .file_connector import FileConnector
from ..error import FileError
from ..log import log_system, LogLevel

log = log_system.get_or_create_logger("file")
log.setLevel(LogLevel.INFO)

MIME = magic.Magic(mime=True)

KPARSE_MODEL = {
    "encoding": {"type": str, "default": "utf-8"},
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

        options = Kparse(kwargs, KPARSE_MODEL)

        self._work_connector: FileConnector = options.get("work_connector")
        self._storage_connector: FileConnector = options.get("storage_connector")

        encoding = options.get("encoding")
        buffering = options.get("buffering")
        self._modes = {
            "w": "wb" if encoding is None else "w",
            "r": "rb" if encoding is None else "r",
            "a": "ab" if encoding is None else "a",
        }

        on = copy.copy(options.get("on"))
        on.append(("before_save", self.on_before_save))

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
        fsrc = self.filename.get_value()
        if fsrc is not None:
            fdst = fsrc + "_copy"
            b.__dict__["filename"].set(fdst)
            _id = b.copy_file_content(
                fsrc, self._work_connector, fdst, b._work_connector
            )
        return b

    def get_content(self) -> str | bytes:
        """Get the file content

        :return: the content of the file
        :rtype: str|bytes
        """
        f = self.filename.get_value()

        log.debug(f"{self.path_name()} file get_content() for {f}")

        # Get file From storage if not there
        if not self._work_connector.has_file(f):
            self.load()
            if not self._work_connector.has_file(f):
                raise FileError(
                    '{0} file "{1}" not found in storage', self.path_name(), f
                )

        return self._work_connector.get(f, self._modes["r"])

    def set_content(self, content: str | bytes) -> None:
        """
        Set the file content
        """
        f = self.filename.get_value()
        mime_type = MIME.from_buffer(content)

        log.debug(f"{self.path_name()} file set_content() for {f} {mime_type}")

        _id = self._work_connector.set(f, self._modes["w"], content)

        if f is None:
            self.filename.set(_id)

        # Set the mime_type
        self.mime_type.set(mime_type)
        # set as modified
        self.modified.set(True)

    def copy_file_content(
        self, fsrc: str, src: FileConnector, fsdt: str, dst: FileConnector
    ) -> str | None:
        """Copy a file from an connector to another

        :param src: _description_
        :type src: FileConnector
        :param dst: _description_
        :type dst: FileConnector
        """

        if not src.has_file(fsrc):
            return None

        chunk_iterator = src.read_chunk(fsrc)
        if chunk_iterator is None:
            return None

        _id = None
        for chunk in chunk_iterator:
            _id = dst.write_chunk(fsdt, chunk)
        return _id

    def load(self) -> None:
        """
        load from the cold storage
        """
        # No cold storage, the storage is directly used
        if self._storage_connector is None:
            return

        f = self.filename.get_value()

        self._work_connector.delete(f)

        self.copy_file_content(f, self._storage_connector, f, self._work_connector)

        # set as not modified
        self.modified.set(False)

    def save(self) -> None:
        """
        Save to the cold storage _storage_connector
        """
        # Nothing to save
        if self.modified.get_value() is False:
            return

        # No cold storage, the storage is directly used
        if self._storage_connector is None:
            return

        f = self.filename.get_value()
        _id = self.copy_file_content(
            f, self._work_connector, f, self._storage_connector
        )
        self.filename.set(_id)

        # set as not modified
        self.modified.set(False)

    def on_before_save(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Try to save the file if possible
        """
        return me.save()
