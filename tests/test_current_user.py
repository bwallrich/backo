"""
test for Flask and routes
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import json
import jwt
from functools import wraps
from flask import Flask, request, jsonify, make_response
from datetime import datetime, timezone, timedelta
from backo import Item, Collection
from backo import DBYmlConnector
from backo import Backoffice, current_user

from stricto import String, Bool


YML_DIR = "/tmp/backo_tests_current_user"


class TestCurrentUser(unittest.TestCase):
    """
    Flask tests
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        # --- DB for user
        self.yml_users = DBYmlConnector(path=YML_DIR)
        self.yml_users.generate_id = lambda o: f"User_{o.name}_{o.surname}"

        # --- DB for sites
        # self.yml_sites = DBYmlConnector(path=YML_DIR)
        # self.yml_sites.generate_id = lambda o: f"Site_{o.name}"

        self.backo = Backoffice("myApp")

        self.users_coll = Collection(
            "users",
            Item(
                {
                    "name": String(),
                    "surname": String(),
                    "male": Bool(
                        default=True,
                    ),
                }
            ),
            self.yml_users,
        )
        self.users_coll.define_view("!surname_only", ["$.name"])

        self.backo.register_collection(self.users_coll)

        self.yml_users.drop()

        self.yml_users.delete_by_id("User_bebert_bebert")

        u = self.backo.users.create({"name": "bebert", "surname": "bebert"})
        self.assertEqual(u._id, "User_bebert_bebert")

        u = self.backo.users.create({"name": "bert1", "surname": "bert1"})
        self.assertEqual(u._id, "User_bert1_bert1")

        u = self.backo.users.create({"name": "bert2", "surname": "bert2"})
        self.assertEqual(u._id, "User_bert2_bert2")

        # set the flask application route
        self.flask = Flask(__name__)
        self.flask.secret_key = "super secret key"

        # Set the login route
        @self.flask.route("/login", methods=["POST"])
        def login():
            d = request.json
            login = d["login"]
            password = d["password"]
            if login != "test":
                return jsonify({"message": "Invalid email or password"}), 401
            if password != "1234":
                return jsonify({"message": "Invalid email or password"}), 401
            token = jwt.encode(
                {
                    "exp": datetime.now(timezone.utc) + timedelta(hours=1),
                    "user": {"_id": "test_id", "login": "test "},
                },
                "myappsecretkey",
                algorithm="HS256",
            )
            response = make_response(json.dumps({"login": "ok"}))
            response.set_cookie("jwt_token", token)
            return response

        def token_required(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                token = request.cookies.get("jwt_token")
                if not token:
                    return jsonify({"message": "Token is missing!"}), 401
                try:
                    data = jwt.decode(token, "myappsecretkey", algorithms=["HS256"])
                except: # pylint: disable=bare-except
                    return jsonify({"message": "Token is invalid!"}), 401

                current_user.set(data["user"])
                return f(*args, **kwargs)

            return decorated

        @self.flask.route("/ping")
        @token_required
        def ping():
            response = make_response(
                json.dumps({"pong": True, "current_user": current_user.get_value()})
            )
            return response

        @self.flask.route("/logout")
        @token_required
        def logout():
            current_user.logout()
            response = make_response(json.dumps({"logout": True}))
            response.delete_cookie("jwt_token")
            return response

        # set the flask application route
        self.backo.add_routes(self.flask, "auth")

        # Set client for testing
        self.ctx = self.flask.app_context()
        self.ctx.push()
        self.client = self.flask.test_client()

    def test_wrong_login(self):
        """
        Test wrong login / password
        """
        response = self.client.post(
            "/login",
            json={"login": "testfake", "password": "1234"},
        )
        self.assertEqual(response.status_code, 401)
        response = self.client.post(
            "/login",
            json={"login": "test", "password": "fakepassword"},
        )
        self.assertEqual(response.status_code, 401)

    def test_non_auth_attempt(self):
        """
        Test not logged error attemps
        """
        response = self.client.get("/ping")
        self.assertEqual(response.status_code, 401)

    def test_login(self):
        """
        Test the login and logout
        """
        response = self.client.post(
            "/login",
            json={"login": "test", "password": "1234"},
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/ping")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["current_user"]["_id"], "test_id")
        response = self.client.get("/logout")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/ping")
        self.assertEqual(response.status_code, 401)
