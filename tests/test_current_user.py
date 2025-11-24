"""
test for Flask and routes
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import json
import jwt
from flask import Flask, request, jsonify, make_response
from datetime import datetime, timezone, timedelta
from backo import Item, Collection
from backo import DBYmlConnector
from backo import Backoffice

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

        # Set the login route
        @self.flask.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                login = request.form['login']
                password = request.form['password']
                if login != "test":
                    return jsonify({'message': 'Invalid email or password'}), 401
                if password != "1234":
                    return jsonify({'message': 'Invalid email or password'}), 401

                token = jwt.encode({'_id': 'test_id', 'exp': datetime.now(timezone.utc) + timedelta(hours=1)},
                                   'myappsecretkey', algorithm="HS256")

                response = make_response(json.dumps({ "login" : "ok" }))
                response.set_cookie('jwt_token', token)

                return response

        @token_required


        # set the flask application route
        self.backo.add_routes(self.flask, "auth")

        # Set client for testing
        self.ctx = self.flask.app_context()
        self.ctx.push()
        self.client = self.flask.test_client()

    def test_login(self):
        """
        Test the login 
        """