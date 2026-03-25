"""
backoffice : The main application
"""

import json
import sys
from functools import wraps
from datetime import datetime, timezone, timedelta
import jwt
from flask import Flask, request, jsonify, make_response, Response

sys.path.insert(1, "../../../backo")


from collections_set import books, users
from backo import Backoffice, current_user, log_system, Log_level

log_system.add_handler(log_system.set_streamhandler())
log_system.setLevel(Log_level.ERROR)


# set the flask application route
flask = Flask("my_media_library")
flask.secret_key = "super secret key"


# --- Set the login route -----
@flask.route("/login", methods=["POST"])
def log_in():
    """check the login and if OK return a jwt token populated with the user data for current_user"""
    d = request.json
    login = d["login"]
    password = d["password"]

    current_user.standalone = True

    # find the user by login in the db
    user = users.select_one({"login": login})

    # Fake auth
    if login != password:
        return jsonify({"message": "Invalid login or password"}), 401

    if user is None:
        user = users.create({"login": login, "roles": ["USER"]})
    current_user.standalone = False

    token = jwt.encode(
        {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "user": {
                "_id": user._id.get_value(),
                "login": user.login.get_value(),
                "roles": user.roles.get_value(),
            },
        },
        "myappsecretkey",
        algorithm="HS256",
    )
    response = make_response(json.dumps({"login": "ok"}))
    response.set_cookie("jwt_token", token)
    return response


def check_user_token() -> None | Response:
    """
    Decode the jwt token and set current_user.
    """
    token = request.cookies.get("jwt_token")
    if not token:
        return jsonify({"message": "Token is missing!"}), 401
    try:
        data = jwt.decode(token, "myappsecretkey", algorithms=["HS256"])
    except:  # pylint: disable=bare-except
        return jsonify({"message": "Token is invalid!"}), 401
    current_user.set(data["user"])
    return None


def token_required(f):
    """Populate current_user with data found in the jwt token"""

    @wraps(f)
    def decorated(*args, **kwargs):
        error_message = check_user_token()
        if error_message is not None:
            return error_message
        return f(*args, **kwargs)

    return decorated


@flask.route("/ping")
@token_required
def ping():
    """
    just a ping
    """
    response = make_response(
        json.dumps({"pong": True, "current_user": current_user.get_value()})
    )
    return response


@flask.route("/logout")
@token_required
def logout():
    """The logout
    clear the jwt in cookie
    """
    current_user.logout()
    response = make_response(json.dumps({"logout": True}))
    response.delete_cookie("jwt_token")
    return response


myapp = Backoffice("media_library")
myapp.add_collection(books)
myapp.add_collection(users)
myapp.add_routes(flask, "", check_user_token)


# ------------------------------------
# Initialisation
# ------------------------------------
current_user.standalone = True
current_user.roles.append("ADMIN")

users.drop()
books.drop()

admin_user = users.select_one({"login": "admin"})
if admin_user is None:
    users.create({"login": "admin", "roles": ["ADMIN", "USER"]})
emp1_user = users.select_one({"login": "emp1"})
if emp1_user is None:
    users.create({"login": "emp1", "roles": ["EMPLOYEE", "USER"]})

first_book = books.select_one({"title": "martine mange des yaourth"})
if first_book is None:
    books.create({"title": "martine mange des yaourth", "pages": 12})


current_user.standalone = False


if __name__ == "__main__":
    flask.run(host="0.0.0.0", port=5000)
