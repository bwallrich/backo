# pylint: disable=relative-beyond-top-level, attribute-defined-outside-init
"""Module providing the BlobFile Class"""

import sys
from werkzeug.datastructures import FileStorage


# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Bytes
from .file_connector import FileConnector
from .file_blob_connector import FileBlobConnector
from .file import File, MIME
from ..error import FileError
from ..log import log_system, LogLevel

log = log_system.get_or_create_logger("file", LogLevel.INFO)


class BlobFile(File):
    """File type

    :param ``**kwargs``:
        See :py:class:`File`

    """

    def __init__(self, **kwargs):
        """
        Object to manage files directly in the data File object.
        
        With this object, file are store with meta_datas ( filename, file_id, size, content_type...) in the DB
        Interesting for small files.
              
        """

        kwargs["work_connector"] = FileBlobConnector()

        File.__init__(self, **kwargs)

        # add the content to the model to store the file content
        self.add_to_model("content", Bytes())

    def get_content(self) -> bytes | None:
        """Get the file content

        :return: the content of the file
        :rtype: str|bytes
        """
        f_id = self.file_id.get_value()
        if f_id is None:
            raise FileError("{0} file doesnt exists (no file_id)", self.path_name())

        return self.content.get_value()

    def _set_content_from_filestorage(self, content: FileStorage) -> None:
        """Set the content of the file from a FileStorage

        :param content: the content
        :type content: FileStorage
        """
        log.debug(f"{self.path_name()} file _set_content_from_filestorage()")

        barray = bytearray(b"")
        chunk = content.read(self._buffers_size)
        log.debug(f"chunk read {chunk}")

        size_read = 0
        while chunk != b"":
            log.debug(f"chunk read {chunk}")
            size_read += len(chunk)
            barray += bytearray(chunk)
            chunk = content.read(self._buffers_size)
        content.close()
        log.debug(f"{self.path_name()} file _set_content_from_filestorage() = {barray}")

        if content.filename is not None:
            self.filename.set(content.filename)

        c = bytes(barray)
        self.content.set(c)
        self.content_type.set(MIME.from_buffer(c))
        self.modified.set(True)
        self.file_id.set("_local")
        self.size.set(len(c))

    def copy_file_content(  # pylint: disable=unused-argument
        self, fsrc: str, src: FileConnector, fsdt: str, dst: FileConnector
    ) -> str | None:
        """Copy a file from an connector to another

        :param src: _description_
        :type src: FileConnector
        :param dst: _description_
        :type dst: FileConnector
        """
        return None

    def load(self) -> None:
        """
        load from the cold storage
        """

    def save(self) -> None:
        """
        Save to the cold storage _storage_connector
        """

    def on_before_save(  # pylint: disable=unused-argument
        self, event_name, root, me, **kwargs
    ):
        """
        Try to save the file if possible
        """
        me.modified = False
