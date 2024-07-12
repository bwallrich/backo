"""
Module providing the Generic() Class
This class must not be used directly
"""
# pylint: disable=wrong-import-position,import-error, wrong-import-order
import sys

sys.path.insert(1, "../../stricto/stricto")

from stricto import Dict, String, List


class CurrentUser(Dict):  # pylint: disable=too-few-public-methods
    """
    The current user Object
    """

    def __init__(self, **kwargs):
        """
        available arguments
        """
        Dict.__init__(
            self,
            {
                "login": String(default=None),
                "user_id": String(default=None),
                "roles": List(String(default=None), default=[]),
            },
            **kwargs
        )

    def has_role(self, role):
        """
        return true if has the role
        """
        return role in self.roles


current_user = CurrentUser()
