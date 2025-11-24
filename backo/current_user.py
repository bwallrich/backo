"""
Module providing the Generic() Class
This class must not be used directly
"""

# pylint: disable=wrong-import-position,import-error, wrong-import-order
import sys

sys.path.insert(1, "../../stricto/stricto")

from stricto import Dict, String, List

from flask import session, request, jsonify
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt_token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, 'myappsecretkey', algorithms=["HS256"])
            session['current_user_id'] = data['_id']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated




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
            **kwargs,
        )

    def has_role(self, role: str) -> bool:
        """
        return true if has the role
        """
        return role in self.roles

    def set_user( self ):
        """
        test
        """
        print(f'Set user session {session.keys}')


class FlaskUser:
    """
    Define with a proxy
    """

    def __init__(self, **kwargs):
        self.users = []

    

flasusers = FlaskUser()

current_user = CurrentUser()
