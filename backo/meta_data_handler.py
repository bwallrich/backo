"""
Module providing the Meta_data_manipulation
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys

from datetime import datetime
from .current_user import current_user
# from .status import StatusType

sys.path.insert(1, "../../stricto")
from stricto import Dict, String, Datetime


class GenericMetaDataHandler:  # pylint: disable=too-many-instance-attributes
    """
    A generic meta Data
    """

    def __init__(self):
        """
        Nothing to do
        """

    def update(self, o):
        """
        Modification of metadata when the object will be created
        """

    def append_schema(self, o):
        """
        Add to the schema
        """


class StandardMetaDataHandler(
    GenericMetaDataHandler
):  # pylint: disable=too-many-instance-attributes
    """
    A Meta data class handle for _meta schema
    """

    def __init__(self):
        """
        Nothing to do
        """

    def update(self, o: Dict) -> None:
        """
        Modification of metadata when the object will be created
        """
        permission_enabled = o._permissions.get_permissions_status()
        now = datetime.now()

        # Disable momentary permissions to change meta_data
        o.disable_permissions()

        # Set creation ctime and owner
        if o._meta.ctime == None:   # pylint: disable=singleton-comparison
            o._meta.ctime = now

        if o._meta.created_by.user_id == None: # pylint: disable=singleton-comparison
            o._meta.created_by.user_id = current_user.user_id.copy()
            o._meta.created_by.login = current_user.login.copy()

        # Set modificattion time and last updater
        o._meta.mtime = now
        o._meta.modified_by.user_id = current_user.user_id.copy()
        o._meta.modified_by.login = current_user.login.copy()

        # Put permission back
        if permission_enabled is True:
            o.enable_permissions()

    def append_schema(self, o: Dict) -> None:
        """
        Add to the schema
        """
        o.add_to_model(
            "_meta",
            Dict(
                {
                    "ctime": Datetime(description="Creation time"),
                    "mtime": Datetime(description="Last modification time"),
                    "created_by": Dict(
                        {"user_id": String(), "login": String(default="ANONYMOUS")},
                        description="Created by",
                    ),
                    "modified_by": Dict(
                        {"user_id": String(), "login": String(default="ANONYMOUS")},
                        description="Modifyied by",
                    ),
                },
                can_modify=False,
                description="Meta data information",
            ),
        )
