import unittest
from flask import Flask, request, jsonify, make_response
import json
import jwt
import sys
import logging
from functools import wraps
from datetime import datetime, timezone, timedelta

sys.path.insert(1, "../../../backo")
sys.path.insert(1, "../../../stricto")


from backo import Backoffice, current_user, log_system

from Collections import books, users


log_system.add_handler(log_system.set_streamhandler())
log_system.setLevel(logging.ERROR)


# set the flask application route
flask = Flask("my_media_library")
flask.secret_key = "super secret key"


# --- Set the login route -----
@flask.route("/login", methods=["POST"])
def login():
    """check the login and if OK return a jwt token populated with the user data for current_user"""
    d = request.json
    login = d["login"]
    password = d["password"]

    current_user.standalone = True

    user = users.select_one({"login": login})

    # Fake auth
    if login != password:
        return jsonify({"message": "Invalid email or password"}), 401

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


def token_required(f):
    """Populate current_user with data found in the jwt token"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("jwt_token")
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            data = jwt.decode(token, "myappsecretkey", algorithms=["HS256"])
        except:  # pylint: disable=bare-except
            return jsonify({"message": "Token is invalid!"}), 401
        current_user.set(data["user"])
        return f(*args, **kwargs)

    return decorated


def check_user_token():
    token = request.cookies.get("jwt_token")
    if not token:
        return jsonify({"message": "Token is missing!"}), 401
    try:
        data = jwt.decode(token, "myappsecretkey", algorithms=["HS256"])
    except:  # pylint: disable=bare-except
        return jsonify({"message": "Token is invalid!"}), 401
    current_user.set(data["user"])


@flask.route("/ping")
@token_required
def ping():
    response = make_response(
        json.dumps({"pong": True, "current_user": current_user.get_value()})
    )
    return response


@flask.route("/logout")
@token_required
def logout():
    """The logout
    clear the kwt in cookie
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

user = users.select_one({"login": "admin"})
if user is None:
    users.create({"login": "admin", "roles": ["ADMIN", "USER"]})
user = users.select_one({"login": "emp1"})
if user is None:
    users.create({"login": "emp1", "roles": ["EMPLOYEE", "USER"]})

book = books.select_one({"title": "martine mange des yaourth"})
if book is None:
    books.create({"title": "martine mange des yaourth", "pages": 12})


current_user.standalone = False


if __name__ == "__main__":
    flask.run(host="0.0.0.0", port=5000)
else:

    class TestAction(unittest.TestCase):
        def __init__(self, *args, **kwargs):
            """
            init this tests
            """
            super().__init__(*args, **kwargs)
            ctx = flask.app_context()
            ctx.push()
            self.client = flask.test_client()

        def login(self, login):
            return self.client.post("/login", json={"login": login, "password": login})

        def logout(self):
            return self.client.get("/logout")

        def test_jwt_fail(self):
            self.logout()
            response = self.client.get("/ping")
            self.assertEqual(response.status_code, 401)

        def test_login_logout(self):
            self.logout()
            self.login("test")
            self.logout()
            response = self.client.get("/ping")
            self.assertEqual(response.status_code, 401)

        def test_emp1_cannot_create_a_user(self):
            self.logout()
            response = self.login("emp1")
            response = self.client.post(
                "/media_library/coll/users", json={"login": "toto1"}
            )
            self.assertEqual(response.status_code, 403)
            self.logout()

        def test_admin_create_users(self):
            self.logout()
            response = self.login("admin")
            response = self.client.post(
                "/media_library/coll/users", json={"login": "toto1"}
            )
            self.assertEqual(response.status_code, 200)
            response = self.client.post(
                "/media_library/coll/users", json={"login": "toto2"}
            )
            self.assertEqual(response.status_code, 200)
            response = self.client.post(
                "/media_library/coll/users", json={"login": "toto3"}
            )
            self.assertEqual(response.status_code, 200)
            response = self.client.post(
                "/media_library/coll/users", json={"login": "toto4"}
            )
            self.assertEqual(response.status_code, 200)
            self.logout()

        def test_emp1_add_books(self):
            self.logout()
            response = self.login("emp1")
            response = self.client.post(
                "/media_library/coll/books",
                json={"title": "martine a la plage 1", "pages": 21},
            )
            self.assertEqual(response.status_code, 200)
            d = json.loads(response.data)
            book_id = d["_id"]
            # self.logout()
            # self.login('test')
            # response=self.client.delete(f"/media_library/coll/books/{book_id}")
            # self.assertEqual(response.status_code, 403)
            # self.logout()
            # self.login('emp1')
            response = self.client.delete(f"/media_library/coll/books/{book_id}")
            self.assertEqual(response.status_code, 200)

            response = self.client.post(
                "/media_library/coll/books",
                json={"title": "martine a la plage 2", "pages": 22},
            )
            self.assertEqual(response.status_code, 200)

            response = self.client.post(
                "/media_library/coll/books",
                json={"title": "martine a la plage 3", "pages": 23},
            )
            self.assertEqual(response.status_code, 200)
            self.logout()

        def test_emp1_borrow_a_book(self):
            self.logout()
            response = self.login("emp1")
            response = self.client.get("/media_library/coll/users?login=toto1")
            results = json.loads(response.data)
            self.assertEqual(results["total"], 1)
            user = results["result"][0]
            response = self.client.get(
                "/media_library/coll/books?title.$reg=martine.*3"
            )
            results = json.loads(response.data)
            self.assertEqual(results["total"], 1)
            book = results["result"][0]

            # response = self.client.post(
            #     f"/media_library/coll/books/_actions/borrow/{book['_id']}",
            #     json={"user_id": user['_id'], "return_date": "test"},
            # )
            # self.assertEqual(response.status_code, 400)

            return_date = datetime.now() + timedelta(days=3)

            response = self.client.post(
                f"/media_library/coll/books/_actions/borrow/{book['_id']}",
                json={"user_id": user["_id"], "return_date": return_date.isoformat()},
            )
            self.assertEqual(response.status_code, 200)

            response = self.client.get(f"/media_library/coll/users/{user['_id']}")
            u = json.loads(response.data)
            self.assertEqual(u["rent"]["books"][0], book["_id"])

            # print(json.dumps(json.loads(response.data), indent=2)
