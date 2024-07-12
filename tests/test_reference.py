"""
test for References()
"""
# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import sys
sys.path.insert(1, "../stricto")

import unittest

from backo import GenericDB
from backo import DBYmlConnector
from backo import App
from backo import Ref, RefsList, DeleteStrategy, Error


from stricto import  String, Bool


class TestReferences(unittest.TestCase):
    """
    DB with references ()
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        # --- DB for user
        self.yml_users = DBYmlConnector(path="/tmp")
        self.yml_users.generate_id = (
            lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
        )

        # --- DB for sites
        self.yml_sites = DBYmlConnector(path="/tmp")
        self.yml_sites.generate_id = lambda o: "Site_" + o.name.get_value()

    def test_references_one_to_many(self):
        """
        creating an app with ref one to many
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users", required=True),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users", field="$.site", ods=DeleteStrategy.MUST_BE_EMPTY
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.users.db.delete_by_id("User_bebert_bebert")

        si = app.sites.new()
        si.create({"name": "moon", "address": "loin"})

        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert", "site": si._id})

        # -- Check if reverse is filled
        si = app.sites.new()
        si.load("Site_moon")
        self.assertEqual(len(si.users), 1)
        self.assertEqual(si.users[0], u._id)

        # -- check if deletion reverse is OK
        u.delete()
        si = app.sites.new()
        si.load("Site_moon")
        self.assertEqual(len(si.users), 0)

        # -- delete site
        si.delete()

    def test_references_one_to_many_strategy_clean(self):
        """
        creating an app with ref one to many
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users", field="$.site", ods=DeleteStrategy.CLEAN_REVERSES
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.users.db.delete_by_id("User_bebert_bebert")

        si = app.sites.new()
        si.create({"name": "moon", "address": "loin"})

        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert", "site": si._id})

        # -- Check if reverse is filled
        si = app.sites.new()
        si.load("Site_moon")
        self.assertEqual(len(si.users), 1)
        self.assertEqual(si.users[0], u._id)

        # -- delete site
        si.delete()

        u = app.users.new()
        u.load("User_bebert_bebert")
        self.assertEqual(u.site, None)

    def test_references_one_to_many_strategy_delete(self):
        """
        creating an app with ref one to many
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users",
                        field="$.site",
                        ods=DeleteStrategy.DELETE_REVERSES_TOO,
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.users.db.delete_by_id("User_bebert_bebert")

        si = app.sites.new()
        si.create({"name": "moon", "address": "loin"})

        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert", "site": si._id})

        # -- Check if reverse is filled
        si = app.sites.new()
        si.load("Site_moon")
        self.assertEqual(len(si.users), 1)
        self.assertEqual(si.users[0], u._id)

        # -- delete site
        si.delete()

        u = app.users.new()
        with self.assertRaises(Error) as e:
            u.load("User_bebert_bebert")
        self.assertEqual(e.exception.message, '_id "User_bebert_bebert" not found')

    def test_references_errors(self):
        """
        creating an app with ref with errors
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users",
                        field="$.site",
                        ods=DeleteStrategy.DELETE_REVERSES_TOO,
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.users.db.delete_by_id("User_bebert_bebert")

        si = app.sites.new()
        si.create({"name": "moon", "address": "loin"})

        u = app.users.new()
        self.assertEqual(u.site.get_root(), u)

        t_id = app.start_transaction()
        u.site._collection = "unknown_coll"
        with self.assertRaises(Error) as e:
            u.create({"name": "bebert", "surname": "bebert", "site": "1234"}, t_id)
        self.assertEqual(e.exception.message, 'Collection "unknown_coll" not found')
        app.rollback_transaction(t_id)

        t_id = app.start_transaction()
        # app.users.db.delete_by_id("User_bebert_bebert")
        u.site._collection = "sites"
        u.site._reverse = "unknown_reverse"
        with self.assertRaises(Error) as e:
            u.create({"name": "bebert", "surname": "bebert", "site": si._id}, t_id)
        self.assertEqual(
            e.exception.message, 'Collection "sites"."unknown_reverse" not found'
        )
        app.rollback_transaction(t_id)

        t_id = app.start_transaction()
        # app.users.db.delete_by_id("User_bebert_bebert")
        u.site._reverse = "users"
        with self.assertRaises(Error) as e:
            u.create({"name": "bebert", "surname": "bebert", "site": "no_ref"}, t_id)
        self.assertEqual(e.exception.message, '_id "no_ref" not found')
        app.rollback_transaction(t_id)
