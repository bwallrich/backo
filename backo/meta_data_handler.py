"""
Module providing the Meta_data_manipulation
"""
# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys

from datetime import datetime
from .current_user import current_user
from .status import StatusType

sys.path.insert(1, "../../stricto")
from stricto import Dict, Int, String


class GenericMetaDataHandler():  # pylint: disable=too-many-instance-attributes
    """
    A generic meta Data
    """

    def __init__(self):
        """
        Nothing to do
        """


    def set_on_create(self, o):
        """
        Modification of metadata when the object will be created
        """

    def set_on_save(self, o):
        """
        Modification of metadata when the object will be created
        """

    def append_schema(self, o):
        """
        Add to the schema
        """


class StandardMetaDataHandler(GenericMetaDataHandler):  # pylint: disable=too-many-instance-attributes
    """
    A Meta data class handle for _meta schema
    """

    def __init__(self):
        """
        Nothing to do
        """

    def on_set(self, value, o):  # pylint: disable=unused-argument
        """
        ctime and created_by cannot be modified by user
        """
        if value is None:
            return {
                'ctime' : 0,
                'mtime' : 0,
                'created_by' : {
                    'user_id' : 0,
                    'login' : "ANONYMOUS"
                },
                'modified_by' : {
                    'user_id' : 0,
                    'login' : "ANONYMOUS"
                }
            }

        return value


    def can_modify_creation_meta(self, value, o):  # pylint: disable=unused-argument
        """
        ctime and created_by cannot be modified by user
        """
        if o._status == StatusType.UNSET:
            return True
        return False

    def set_on_create(self, o):
        """
        Modification of metadata when the object will be created
        """
        o._meta.created_by.user_id = current_user.user_id.copy()
        o._meta.created_by.login = current_user.login.copy()
        o._meta.modified_by.user_id = current_user.user_id.copy()
        o._meta.modified_by.login = current_user.login.copy()

        timestamp = int(datetime.timestamp(datetime.now()))
        o._meta.ctime = timestamp
        o._meta.mtime = timestamp

    def set_on_save(self, o):
        """
        Modification of metadata when the object will be created
        """
        timestamp = int(datetime.timestamp(datetime.now()))
        o._meta.mtime = timestamp
        o._meta.modified_by.user_id = current_user.user_id.copy()
        o._meta.modified_by.login = current_user.login.copy()


    def append_schema(self, o):
        """
        Add to the schema
        """
        o.add_to_model(
            "_meta",
            Dict(
                {
                    "ctime": Int(can_modify=self.can_modify_creation_meta),
                    "mtime": Int(),
                    "created_by": Dict(
                        {"user_id": String(), "login": String()},
                        can_modify=self.can_modify_creation_meta,
                    ),
                    "modified_by": Dict({"user_id": String(), "login": String()}),
                }, transform=self.on_set
            )
        )
