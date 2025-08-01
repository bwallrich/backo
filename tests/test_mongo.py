"""
test for CRUD()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import time


from backo import Item, Collection
from backo import DBMongoConnector
from backo import App, Error, current_user

from stricto import String, Bool  # , Error as StrictoError


class TestMongo(unittest.TestCase):
    """
    DB Mongo crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        # --- DB for user
        self.db_users = DBMongoConnector(
            connection_string="mongodb://localhost:27017/testMongo", collection="Users"
        )

        # --- DB for sites
        self.db_site = DBMongoConnector(
            connection_string="mongodb://localhost:27017/testMongo", collection="Sites"
        )

    def test_error_db_connect(self):
        """
        try to connect error
        """
        a = DBMongoConnector(
            connection_string="mongodb://localhost:666/testMongo",
            collection="test",
            serverSelectionTimeoutMS=1,
        )
        with self.assertRaises(Error) as e:
            a.connect()
        self.assertEqual(
            e.exception.message,
            "Mongo connection error at mongodb://localhost:666/testMongo",
        )
        b = self.db_users.connect()
        self.assertNotEqual(b["version"], None)

    def test_errors_on_create_delete(self):
        """
        create
        and delete errors
        """

        app = App("myApp")
        user_model = Item(
            {"name": String(), "surname": String(), "male": Bool(default=True)}
        )
        coll_users = Collection("users", user_model, self.db_users)
        app.register_collection(coll_users)

        coll_users.drop()

        with self.assertRaises(Error) as e:
            self.db_users.delete_by_id("42")
        self.assertEqual(
            e.exception.message,
            "Mongo connection error while Users.delete_one() mongodb://localhost:27017/testMongo",
        )
        # delete a non exinsting user
        self.assertEqual(self.db_users.delete_by_id("66a8ee2614c85110d75b9cf8"), False)

        # Load a non existing user
        with self.assertRaises(Error) as e:
            self.db_users.get_by_id("42")
        self.assertEqual(
            e.exception.message,
            "Mongo connection error while Users.find_one() mongodb://localhost:27017/testMongo",
        )
        with self.assertRaises(Error) as e:
            self.db_users.get_by_id("66a8ee2614c85110d75b9cf8")
        self.assertEqual(
            e.exception.message, '_id "66a8ee2614c85110d75b9cf8" not found'
        )

        v = app.users.new()
        v.create({"name": "bebert", "surname": "bebert"})
        self.assertNotEqual(v._id, None)
        self.assertNotEqual(v._meta, None)
        u = app.users.new()
        u.load(v._id)
        self.assertEqual(v._id, u._id)
        self.assertEqual(v, u)

    def test_create_delete(self):
        """
        create
        and delete
        """

        app = App("myApp")

        app.register_collection(
            Collection(
                "users",
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)}
                ),
                self.db_users,
            )
        )

        app.users.drop()

        current_user.login = "Roger"
        current_user.user_id = "1234"

        # -- creation
        u = app.new("users")
        u.create({"name": "bebert", "surname": "bebert"})
        v = app.users.new()

        v.load(u._id)
        self.assertEqual(v, u)
        self.assertEqual(v.male, True)
        self.assertEqual(v._meta.mtime, v._meta.ctime)
        self.assertEqual(v._meta.created_by.login, "Roger")
        self.assertEqual(v._meta.created_by.user_id, "1234")
        self.assertEqual(v._meta.modified_by.login, "Roger")
        self.assertEqual(v._meta.modified_by.user_id, "1234")

        # -- change the mtime
        time.sleep(1.1)
        current_user.login = "Mary"
        current_user.user_id = "4321"

        # modification
        u.male = False
        u.save()
        v = app.users.new()
        v.load(u._id)
        self.assertEqual(v.male, False)
        self.assertEqual(v._meta.mtime > v._meta.ctime, True)
        self.assertEqual(v._meta.created_by.login, "Roger")
        self.assertEqual(v._meta.created_by.user_id, "1234")
        self.assertEqual(v._meta.modified_by.login, "Mary")
        self.assertEqual(v._meta.modified_by.user_id, "4321")

        # -- delete
        u.delete()

    def test_select(self):
        """
        select
        """

        app = App("myApp")
        app.register_collection(
            Collection(
                "users",
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)}
                ),
                self.db_users,
            )
        )

        app.users.drop()

        current_user.login = "Roger"
        current_user.user_id = "1234"

        # -- creation
        u = app.new("users")
        u.create({"name": "bebert1", "surname": "bebert"})
        u = app.new("users")
        u.create({"name": "bebert2", "surname": "bebert"})
        u = app.new("users")
        u.create({"name": "bebert3", "surname": "Joe"})
        u = app.new("users")
        u.create({"name": "bebert4", "surname": "Joe"})
        u = app.new("users")
        u.create({"name": "bebert5", "surname": "Joe"})
        u = app.new("users")
        u.create({"name": "bebert6", "surname": "Al"})
        u = app.new("users")
        u.create({"name": "bebert7", "surname": "Al"})

        result = app.users.select({"surname": "Al"})
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["result"]), 2)
        for o in result["result"]:
            self.assertEqual(type(o), Item)
            self.assertEqual(o.surname, "Al")

        # check pagination
        result = app.users.select({"surname": "Al"}, 1, 0)
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["result"]), 1)
        for o in result["result"]:
            self.assertEqual(type(o), Item)
            self.assertEqual(o.surname, "Al")

        # check not found
        result = app.users.select({"surname_not_found": "Al"})
        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["result"]), 0)
        result = app.users.select({"surname": "Al_not_found"})
        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["result"]), 0)
