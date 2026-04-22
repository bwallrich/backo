"""
test for Flask and routes
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import io
import json
import os
from flask import Flask

# get the resources folder in the tests folder

from backo import Item, Collection
from backo import DBYmlConnector
from backo import Backoffice, current_user, Action, Selection

from backo import String, Bool

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

        # SELECTION
        sel = Selection(["$.surname"], filter={"name": ("$reg", r"bert")})
        self.users_coll.register_selection("bert_only", sel)

        # ACTION
        def change_surname(action, o, **kwargs):  # pylint: disable=unused-argument
            """
            Do the increment
            """
            o.surname = action.new_surname
            o.save(**kwargs)

        change_surname_action = Action(
            {"new_surname": String(required=True)},
            change_surname,
            can_execute=lambda self, right_name, action, o: True,
        )
        self.users_coll.register_action("change_surname", change_surname_action)

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
        self.backo.build_routes(self.flask)

        # Set client for testing
        self.ctx = self.flask.app_context()
        self.ctx.push()
        self.client = self.flask.test_client()

    def test_get_by_id(self):
        """
        get by id
        """

        response = self.client.get("/myApp/users/User_bebert_bebert")
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
            "/myApp/users", json={"name": 23, "surname": "bert3"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            str(response.data, "utf-8"),
            'TypeError("$.name: Must be a string (value="23")")',
        )

        response = self.client.post(
            "/myApp/users", json={"name": "bert3", "surname": "bert3"}
        )
        self.assertEqual(response.status_code, 200)

        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "bert3")
        self.assertEqual(u.surname, "bert3")

        response = self.client.put(
            "/myApp/users", json={"name": "bert3", "surname": "hector"}
        )
        self.assertEqual(response.status_code, 405)

        response = self.client.put(
            "/myApp/users/idnotfound", json={"name": "bert3", "surname": "hector"}
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.put(
            f"/myApp/users/{u._id}", json={"name": "bert4", "surname": "hector"}
        )
        self.assertEqual(response.status_code, 200)

        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "bert4")
        self.assertEqual(u.surname, "hector")

        response = self.client.delete("/myApp/users")
        self.assertEqual(response.status_code, 405)

        response = self.client.delete("/myApp/users/idnotfound")
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(f"/myApp/users/{u._id}")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f"/myApp/users/{u._id}")
        self.assertEqual(response.status_code, 404)

    def test_patch(self):
        """
        create an object with a post, then patch it
        """
        # post error
        response = self.client.post(
            "/myApp/users", json={"name": "bert5", "surname": "bert5"}
        )
        self.assertEqual(response.status_code, 200)
        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "bert5")
        self.assertEqual(u.surname, "bert5")

        response = self.client.patch(
            f"/myApp/users/{u._id}",
            json={"op": "replace", "path": "$.name", "value": "toto"},
        )
        self.assertEqual(response.status_code, 200)
        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "toto")
        self.assertEqual(u.surname, "bert5")

        response = self.client.patch(
            f"/myApp/users/{u._id}",
            json=[{"op": "replace", "path": "$.surname", "value": "zaza"}],
        )
        self.assertEqual(response.status_code, 200)
        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertIsNotNone(u._id)
        self.assertEqual(u.name, "toto")
        self.assertEqual(u.surname, "zaza")

        response = self.client.delete(f"/myApp/users/{u._id}")
        self.assertEqual(response.status_code, 200)

    def test_get_wrong_url(self):
        """
        wrong url
        """

        response = self.client.get("/myApp/usnotexistcollers/User_bebert_bebert")
        self.assertEqual(response.status_code, 404)

        response = self.client.post("/myApp/usnotexistcollers/User_bebert_bebert")
        self.assertEqual(response.status_code, 404)

        response = self.client.delete("/myApp/users/")
        self.assertEqual(response.status_code, 404)

    def test_get_by_id_view(self):
        """
        add a user in the DB and get it
        """

        response = self.client.get(
            "/myApp/users/User_bebert_bebert?_view=surname_only&toto=1&toto=2"
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
        response = self.client.get("/myApp/users/User_not_exists")
        self.assertEqual(response.status_code, 404)

    def test_select_route(self):
        """
        do a select
        """
        response = self.client.get("/myApp/users?_page=11")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 3)

    def test_select_route_filter(self):
        """
        do a select
        """
        response = self.client.get("/myApp/users?name=bert1")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 1)

    def test_select_route_filter_1(self):
        """
        do a select
        """
        response = self.client.get("/myApp/users?name.$reg=b")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 3)

        response = self.client.get("/myApp/users?name.$reg=b&_page=2")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 2)

        response = self.client.get("/myApp/users?name.$reg=b&_page=2&_skip=2")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 3)

        l = self.backo.users.set(results["result"])
        self.assertEqual(len(l), 1)

    def test_select_route_filter_sel(self):
        """
        do a select on a selection
        """
        response = self.client.get("/myApp/users/_selections/bert_only")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 2)
        response = self.client.get("/myApp/users/_selections/bert_only?name.$reg=.*1")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)

    def test_select_route_filter_post(self):
        """
        do a select on a selection with a post
        """
        response = self.client.post("/myApp/users/_selections/bert_only", json={})
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 2)
        response = self.client.post(
            "/myApp/users/_selections/bert_only", json={"name": ("$reg", ".*1")}
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)

    def test_check_route_filter(self):
        """
        do a check
        """
        response = self.client.post(
            "/myApp/users/_check",
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
            "/myApp/users/_check",
            json={"item": {"name": "bert3", "surname": 21}, "path": "$.surname"},
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["error"], '$.surname: Must be a string (value="21")')

    def test_current_meta_route(self):
        """
        get current_meta for an object
        """
        response = self.client.post(
            "/myApp/users/_meta",
            json={"name": "bert3", "surname": 21},
        )
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["exists"], True)

    def test_error_action_route(self):
        """
        test an arror on actions route
        """
        response = self.client.post(
            "/myApp/users/_actions/false_action_name/123",
            json={"new_surname": "bert_new"},
        )
        self.assertEqual(response.status_code, 400)

    def test_error_action_route_false_id(self):
        """
        test an arror on actions route
        """
        response = self.client.post(
            "/myApp/users/_actions/change_surname/123",
            json={"new_surname": "bert_new"},
        )
        self.assertEqual(response.status_code, 404)

    def test_error_action_route_wrong_content(self):
        """
        test an arror on actions route
        """
        response = self.client.post(
            "/myApp/users/_actions/change_surname/123",
            json={"new_surname_error": "bert_new"},
        )
        self.assertEqual(response.status_code, 400)

    def test__action_route(self):
        """
        test an arror on actions route
        """

        response = self.client.post(
            "/myApp/users",
            json={"name": "action_name", "surname": "action_surname"},
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/myApp/users/_actions/change_surname/User_action_name_action_surname",
            json={"new_surname": "bert_new"},
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/myApp/users/User_action_name_action_surname")
        self.assertEqual(response.status_code, 200)

        u = self.backo.users.new_item()
        u.set(json.loads(response.data))
        self.assertEqual(u.surname, "bert_new")

        response = self.client.delete(f"/myApp/users/{u._id}")
        self.assertEqual(response.status_code, 200)
