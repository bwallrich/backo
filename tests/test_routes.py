"""
test for Flask and routes
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import json
from flask import Flask

from backo import Item, Collection
from backo import DBYmlConnector
from backo import Backoffice, current_user

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

        # ignore sessions for this campaign of tests.
        current_user.standalone = True

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

        # set the flask route
        self.flask = Flask(__name__)
        self.backo.add_routes(self.flask)

        # Set client for testing
        self.ctx = self.flask.app_context()
        self.ctx.push()
        self.client = self.flask.test_client()

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
        self.assertEqual(rep["total"], 0)

    def test_get_by_id(self):
        """
        get by id
        """

        response = self.client.get("/myApp/coll/users/User_bebert_bebert")
        self.assertEqual(response.status_code, 200)

        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertEqual(u.name, "bebert")

    def test_create_modify_delete_post(self):
        """
        create an object with a post, modify with a put and delete it
        """
        # post error
        response = self.client.post(
            "/myApp/coll/users", json={"name": 23, "surname": "bert3"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data, "utf-8"), 'TypeError("Must be a string")')

        response = self.client.post(
            "/myApp/coll/users", json={"name": "bert3", "surname": "bert3"}
        )
        self.assertEqual(response.status_code, 200)

        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "bert3")
        self.assertEqual(u.surname, "bert3")

        response = self.client.put(
            "/myApp/coll/users", json={"name": "bert3", "surname": "hector"}
        )
        self.assertEqual(response.status_code, 405)

        response = self.client.put(
            "/myApp/coll/users/idnotfound", json={"name": "bert3", "surname": "hector"}
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.put(
            f"/myApp/coll/users/{u._id}", json={"name": "bert4", "surname": "hector"}
        )
        self.assertEqual(response.status_code, 200)

        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "bert4")
        self.assertEqual(u.surname, "hector")

        response = self.client.delete("/myApp/coll/users")
        self.assertEqual(response.status_code, 405)

        response = self.client.delete("/myApp/coll/users/idnotfound")
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(f"/myApp/coll/users/{u._id}")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f"/myApp/coll/users/{u._id}")
        self.assertEqual(response.status_code, 404)

    def test_patch(self):
        """
        create an object with a post, then patch it
        """
        # post error
        response = self.client.post(
            "/myApp/coll/users", json={"name": "bert5", "surname": "bert5"}
        )
        self.assertEqual(response.status_code, 200)
        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "bert5")
        self.assertEqual(u.surname, "bert5")

        response = self.client.patch(
            f"/myApp/coll/users/{u._id}",
            json={"op": "replace", "path": "$.name", "value": "toto"},
        )
        self.assertEqual(response.status_code, 200)
        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "toto")
        self.assertEqual(u.surname, "bert5")

        response = self.client.patch(
            f"/myApp/coll/users/{u._id}",
            json=[{"op": "replace", "path": "$.surname", "value": "zaza"}],
        )
        self.assertEqual(response.status_code, 200)
        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "toto")
        self.assertEqual(u.surname, "zaza")

        response = self.client.delete(f"/myApp/coll/users/{u._id}")
        self.assertEqual(response.status_code, 200)

    def test_get_wrong_url(self):
        """
        wrong url
        """

        response = self.client.get("/myApp/coll/usnotexistcollers/User_bebert_bebert")
        self.assertEqual(response.status_code, 404)

        response = self.client.post("/myApp/coll/usnotexistcollers/User_bebert_bebert")
        self.assertEqual(response.status_code, 404)

        response = self.client.delete("/myApp/coll/users/")
        self.assertEqual(response.status_code, 404)

    def test_get_by_id_view(self):
        """
        add a user in the DB and get it
        """

        response = self.client.get(
            "/myApp/coll/users/User_bebert_bebert?_view=surname_only&toto=1&toto=2"
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
        response = self.client.get("/myApp/coll/users/User_not_exists")
        self.assertEqual(response.status_code, 404)

    def test_select_route(self):
        """
        do a select
        """
        response = self.client.get("/myApp/coll/users?_page=11")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 3)

    def test_select_route_filter(self):
        """
        do a select
        """
        response = self.client.get("/myApp/coll/users?name=bert1")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 1)

    def test_select_route_filter_1(self):
        """
        do a select
        """
        response = self.client.get("/myApp/coll/users?name.$reg=b")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 3)

        response = self.client.get("/myApp/coll/users?name.$reg=b&_page=2")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 2)

        response = self.client.get("/myApp/coll/users?name.$reg=b&_page=2&_skip=2")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 1)

    def test_check_route_filter(self):
        """
        do a check
        """
        response = self.client.post(
            "/myApp/coll/users/_check",
            json={"item": {"name": "bert3", "surname": "hector"}, "path": "$.surname"},
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["error"], None)

    def test_check_route_filter_error(self):
        """
        do a check with error
        """
        response = self.client.post(
            "/myApp/coll/users/_check",
            json={"item": {"name": "bert3", "surname": 21}, "path": "$.surname"},
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["error"], "Must be a string")

    def test_current_meta_route(self):
        """
        get current_meta for an object
        """
        response = self.client.post(
            "/myApp/coll/users/_meta",
            json={"name": "bert3", "surname": 21},
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["exists"], True)
