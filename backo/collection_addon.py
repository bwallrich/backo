"""
The Collection module
"""

# pylint: disable=logging-fstring-interpolation
import sys

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Permissions

from .log import log_system, LogLevel


log = log_system.get_or_create_logger("select", LogLevel.INFO)


class CollectionAddon:
    """
    The parent object for Selection, actions
    """

    def __init__(self):
        """
        available arguments
        """
        self._permissions = Permissions()

        # Those values are set by register_... in collection.
        self.backoffice = None
        self.name = None
        self.collection = None

        # Enable directly all permissions
        self._permissions.enable()

    def is_allowed_to(self, right_name: str, root: any = None) -> bool:
        """
        check the right "right_name"
        """
        rep = self._permissions.is_allowed_to(right_name, root)

        # --- the result must be a bool
        if rep is None:
            return False
        return rep

    def is_strictly_allowed_to(self, right_name: str) -> bool:
        """
        Return the right only if a boolean. If a function, don't call it and return None.
        """
        right = self._permissions.get(right_name, None)
        if isinstance(right, bool):
            return right

        return None
