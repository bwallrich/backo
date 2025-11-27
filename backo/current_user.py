"""
Module providing the Generic() Class
This class must not be used directly
"""

# pylint: disable=wrong-import-position,import-error, wrong-import-order, no-member
import sys
from flask import session

sys.path.insert(1, "../../stricto/stricto")

from stricto import Dict, String, List
from .error import Error, ErrorType

ANONYMOUS_DATA = {"_id": "000", "login": "ANONYMOUS", "roles": []}


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


class CurrentUserWrapper:
    """
    Wrap the currentUser per session
    """

    def __init__(self, obj: CurrentUser):
        """
        initialisation of the wrapper with can work in standalone mode
        or with sessions
        """
        # stadalone = False mean use session to retrieve user. standalone = True use for testing only
        self.standalone = False
        self.user_without_session = obj.copy()
        self.anonymous = obj.copy()
        self.administrator = obj.copy()
        self.users = {}

    def reset(self, obj: CurrentUser):
        """
        remap
        """
        self.user_without_session = obj.copy()
        self.anonymous = obj.copy()
        self.administrator = obj.copy()

    def retrieve_current_user(self) -> CurrentUser:
        """
        retrieve the current user with the session_id
        """
        if self.standalone is True:
            return self.user_without_session

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
            self.user_without_session.set(data)
            return

        u = self.anonymous.copy()
        u.set(data)
        session["current_user_id"] = u._id.get_value()
        self.users[u._id.get_value()] = u

    def __getattr__(self, k):
        """
        replicate all atributes from value, but prefere self attribute first.
        """
        if k == "reset":
            return self.reset
        if k == "standalone":
            return self.standalone
        if k == "retrieve_current_user":
            return self.retrieve_current_user
        if k == "set":
            return self.set
        if k == "logout":
            return self.logout

        u = self.retrieve_current_user()
        return u.__getattr__(k)

    def __setattr__(self, name, value):
        """
        Wrapp all attribute to the current_session_user
        """
        if name in [
            "standalone",
            "user_without_session",
            "anonymous",
            "administrator",
            "users",
        ]:
            self.__dict__[name] = value
            return None

        u = self.retrieve_current_user()
        return u.__setattr__(name, value)


current_user = CurrentUserWrapper(CurrentUser())
current_user.anonymous.set(ANONYMOUS_DATA)
current_user.user_without_session.set(ANONYMOUS_DATA)
