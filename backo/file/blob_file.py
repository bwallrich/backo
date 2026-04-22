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

log = log_system.get_or_create_logger("file", LogLevel.DEBUG)


class BlobFile(File):
    """File type

    :param ``**kwargs``:
        See :py:class:`GenericType`

    :Specifics Arguments:
        * *stotrage* (``str``) --
          the directory to store the file

    """

    def __init__(self, **kwargs):
        """Constructor method"""

        kwargs["work_connector"] = FileBlobConnector()
        kwargs["encoding"] = "utf-8"

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
            raise FileError("{0} file doesnt exists", self.path_name())

        return self.content.get_value()

    def _set_content_from_bytes(self, content: bytes) -> None:
        self.content.set(content)
        self.mime_type = MIME.from_buffer(content)
        self.modified = True
        self.file_id = "_local"

    def _set_content_from_str(self, content: str) -> None:
        return self._set_content_from_bytes(content.encode("utf-8"))

    def _set_content_from_FileStorage(self, content: FileStorage) -> None:
        """Set the content of the file from a FileStorage

        :param content: the content
        :type content: FileStorage
        :return: ( _id, mime_types )
        :rtype: tuple
        """
        log.debug(f"{self.path_name()} file _set_content_from_FileStorage()")

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
        log.debug(f"{self.path_name()} file _set_content_from_FileStorage() = {barray}")

        self._set_content_from_bytes(bytes(barray))

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
