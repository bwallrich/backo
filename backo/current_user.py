"""
Module providing the Generic() Class
This class must not be used directly
"""

# pylint: disable=wrong-import-position,import-error, wrong-import-order
import sys

from flask import session

sys.path.insert(1, "../../stricto/stricto")

from stricto import Dict, String, List
from .error import Error, ErrorType


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
                "_id": String(default=None),
                "login": String(default=None),
                "roles": List(String(default=None), default=[]),
            },
            **kwargs,
        )

    def has_role(self, role: str) -> bool:
        """
        return true if has the role
        """
        return role in self.roles


ANONYMOUS_USER = CurrentUser()
ANONYMOUS_USER.set({"_id": "000", "login": "ANONYMOUS", "roles": []})
user_without_session = ANONYMOUS_USER.copy()


class CurrentUserWrapper:
    """
    Wrap the currentUser per session
    """

    def __init__(self):

        # stadalone = False mean use session to retrieve user. standalone = True use for testing only
        self.standalone = False
        self.users = {}

    def retrieve_current_user(self) -> CurrentUser:
        """
        retrieve the current user with the session_id
        """
        if self.standalone is True:
            return user_without_session

        session_user_id = session.get("current_user_id", None)
        if session_user_id is None:
            raise Error(ErrorType.NO_SESSION_ID, "No session id for authentication")
        u = self.users.get(session_user_id, None)
        if u is None:
            raise Error(
                ErrorType.SESSION_NOT_AUTHENTICATED, "Session not authenticated"
            )

        return u

    def logout(self) -> None:
        """
        erase the user from the db
        """
        if self.standalone is True:
            return

        session_user_id = session.get("current_user_id", None)
        if session_user_id is not None:
            del self.users[session_user_id]

    def set(self, data) -> None:
        """
        Set the user and save it into the database
        """
        if self.standalone is True:
            user_without_session.set(data)
            return

        u = CurrentUser()
        u.set(data)
        session["current_user_id"] = u._id.get_value()
        self.users[u._id.get_value()] = u

    def __getattr__(self, k):
        """
        replicate all atributes from value, but prefere self attribute first.
        """
        if k == "standalone":
            return self.standalone
        if k == "retrieve_current_user":
            return self.retrieve_current_user
        if k == "set":
            return self.set
        if k == "logout":
            return self.logout

        u = self.retrieve_current_user()
        return getattr(u, k, None)


current_user = CurrentUserWrapper()
