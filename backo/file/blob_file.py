# pylint: disable=relative-beyond-top-level, attribute-defined-outside-init
"""Module providing the BlobFile Class"""

import sys


# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Bytes
from .file_connector import FileConnector
from .file_blob_connector import FileBlobConnector
from .file import File, MIME
from ..log import log_system, LogLevel

log = log_system.get_or_create_logger("file")
log.setLevel(LogLevel.INFO)


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

        # Set a fake filename
        self.__dict__["filename"].set("_local")

    def __copy__(self):
        """remap copy to make a copy of the file too

        :return: _description_
        :rtype: _type_
        """
        b = super().__copy__()

        b.__dict__["filename"].set("_local")
        b.__dict__["content"].set(self.content.get_value())
        return b

    def get_content(self) -> str | bytes:
        """Get the file content

        :return: the content of the file
        :rtype: str|bytes
        """
        f = self.filename.get_value()

        log.debug(f"{self.path_name()} blobfile get_content() for {f}")
        v = self.content.get_value()
        if v is None:
            return None

        if self.encoding.get_value():
            return v.decode(self.encoding.get_value())
        return v

    def set_content(self, content: str | bytes) -> None:
        """
        Set the file content
        """
        f = self.filename.get_value()
        mime_type = MIME.from_buffer(content)

        log.debug(f"{self.path_name()} blobfile set_content() for {f} {mime_type}")

        # Set the mime_type
        self.mime_type.set(mime_type)
        # set as modified
        self.modified.set(True)
        if self.encoding.get_value():
            self.content.set(content.encode(self.encoding.get_value()))
        else:
            self.content.set(content)

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
