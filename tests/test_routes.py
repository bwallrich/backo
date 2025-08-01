"""
test for Flask and routes
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import json
from flask import Flask

from backo import Item, Collection
from backo import DBYmlConnector
from backo import App

from stricto import String, Bool

YML_DIR = "/tmp/backo_tests_routes"


class TestRoutes(unittest.TestCase):
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
        self.yml_users.generate_id = (
            lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
        )

        # --- DB for sites
        # self.yml_sites = DBYmlConnector(path=YML_DIR)
        # self.yml_sites.generate_id = lambda o: "Site_" + o.name.get_value()

        self.backo = App("myApp")

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

        # set the app route
        self.app = Flask(__name__)
        self.backo.add_routes(self.app)

        # Set client for testing
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()

    def test_select(self):
        """
        Do a selection with different filters
        """
        self.yml_users.drop()

        u = self.backo.users.create({"name": "bebert", "surname": "bebert"})
        self.assertEqual(u._id, "User_bebert_bebert")

        u = self.backo.users.create({"name": "bert1", "surname": "bert1"})
        self.assertEqual(u._id, "User_bert1_bert1")

        u = self.backo.users.create({"name": "bert2", "surname": "bert2"})
        self.assertEqual(u._id, "User_bert2_bert2")

        rep = self.users_coll.select(None, {})
        self.assertEqual(rep["total"], 3)

        rep = self.users_coll.select(None, {"name": "bebert"})
        self.assertEqual(rep["total"], 1)
        rep = self.users_coll.select(None, {"name": ("$reg", r"bert.*")})
        self.assertEqual(rep["total"], 2)
        rep = self.users_coll.select(None, None)
        self.assertEqual(rep["total"], 3)

    def test_get_by_id(self):
        """
        add a user in the DB and get it
        """

        response = self.client.get("/users/User_bebert_bebert")
        self.assertEqual(response.status_code, 200)

        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertEqual(u.name, "bebert")

    def test_get_by_id_view(self):
        """
        add a user in the DB and get it
        """

        response = self.client.get(
            "/users/User_bebert_bebert?_view=surname_only&toto=1&toto=2"
        )
        self.assertEqual(response.status_code, 200)

        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertEqual(u.name, None)
        self.assertEqual(u.surname, "bebert")

    def test_get_not_found_by_id(self):
        """
        add a user in the DB and get it
        """
        response = self.client.get("/users/User_not_exists")
        self.assertEqual(response.status_code, 204)

    def test_select_route(self):
        """
        do a select
        """
        response = self.client.get("/users?_page=11")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 3)

    def test_select_route_filter(self):
        """
        do a select
        """
        response = self.client.get("/users?name=bert1")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 1)

    def test_select_route_filter_1(self):
        """
        do a select
        """
        response = self.client.get("/users?name.$reg=b")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 3)

        response = self.client.get("/users?name.$reg=b&_page=2")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 2)

        response = self.client.get("/users?name.$reg=b&_page=2&_skip=2")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 1)
