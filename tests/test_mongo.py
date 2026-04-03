"""
test for CRUD()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import time


from backo import Item, Collection
from backo import DBMongoConnector
from backo import Backoffice, NotFoundError, DBError, current_user

from backo import String, Bool  # , Error as StrictoError


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

    def tearDown(self):
        self.db_site.close()
        self.db_users.close()
        return super().tearDown()

    def test_error_db_connect(self):
        """
        try to connect error
        """
        a = DBMongoConnector(
            connection_string="mongodb://localhost:666/testMongo",
            collection="test",
            serverSelectionTimeoutMS=1,
        )
        with self.assertRaises(DBError) as e:
            a.connect()
        self.assertEqual(
            e.exception.to_string(),
            'Mongo connection error at "mongodb://localhost:666/testMongo"',
        )
        a.close()
        b = self.db_users.connect()
        self.assertNotEqual(b["version"], None)

    def test_errors_on_create_delete(self):
        """
        create
        and delete errors
        """

        backoffice = Backoffice("myApp")
        user_model = Item(
            {"name": String(), "surname": String(), "male": Bool(default=True)}
        )
        coll_users = Collection("users", user_model, self.db_users)
        backoffice.register_collection(coll_users)

        coll_users.drop()

        # ignore sessions for this campaign of tests.
        current_user.standalone = True

        with self.assertRaises(DBError) as e:
            self.db_users.delete_by_id("42")
        self.assertEqual(
            e.exception.to_string(),
            'Mongo connection error while "Users.delete_one()"',
        )
        # delete a non exinsting user
        self.assertEqual(self.db_users.delete_by_id("66a8ee2614c85110d75b9cf8"), False)

        # Load a non existing user
        with self.assertRaises(DBError) as e:
            self.db_users.get_by_id("42")
        self.assertEqual(
            e.exception.to_string(),
            'Mongo connection error while "Users.find_one()"',
        )
        with self.assertRaises(NotFoundError) as e:
            self.db_users.get_by_id("66a8ee2614c85110d75b9cf8")
        self.assertEqual(
            e.exception.to_string(), '_id "66a8ee2614c85110d75b9cf8" not found in collection "Users"'
        )

        v = backoffice.users.create({"name": "bebert", "surname": "bebert"})
        self.assertNotEqual(v._id, None)
        self.assertNotEqual(v._meta, None)
        u = backoffice.users.new()
        u.load(v._id)
        self.assertEqual(v._id, u._id)
        self.assertEqual(v, u)

    def test_create_delete(self):
        """
        create
        and delete
        """

        backoffice = Backoffice("myApp")

        backoffice.register_collection(
            Collection(
                "users",
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)}
                ),
                self.db_users,
            )
        )

        backoffice.users.drop()

        # ignore sessions for this campaign of tests.
        current_user.standalone = True

        current_user.login = "Roger"
        current_user._id = "1234"

        # -- creation
        u = backoffice.users.create({"name": "bebert", "surname": "bebert"})
        v = backoffice.users.new()

        v.load(u._id)

        self.assertEqual(v.male, True)
        self.assertEqual(v._meta.mtime, v._meta.ctime)
        self.assertEqual(v._meta.mtime, u._meta.mtime)
        self.assertEqual(v._meta.ctime, u._meta.ctime)
        self.assertEqual(v._meta.created_by.login, "Roger")
        self.assertEqual(v._meta.created_by._id, "1234")
        self.assertEqual(v._meta.modified_by.login, "Roger")
        self.assertEqual(v._meta.modified_by._id, "1234")

        # -- change the mtime
        time.sleep(1.1)
        current_user.login = "Mary"
        current_user._id = "4321"

        # modification
        u.male = False
        u.save()
        v = backoffice.users.new()
        v.load(u._id)
        self.assertEqual(v.male, False)
        self.assertEqual(v._meta.mtime > v._meta.ctime, True)
        self.assertEqual(v._meta.created_by.login, "Roger")
        self.assertEqual(v._meta.created_by._id, "1234")
        self.assertEqual(v._meta.modified_by.login, "Mary")
        self.assertEqual(v._meta.modified_by._id, "4321")

        # -- delete
        u.delete()

    def test_select(self):
        """
        select
        """

        backoffice = Backoffice("myApp")
        backoffice.register_collection(
            Collection(
                "users",
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)}
                ),
                self.db_users,
            )
        )

        backoffice.users.drop()

        # ignore sessions for this campaign of tests.
        current_user.standalone = True

        current_user.login = "Roger"
        current_user._id = "1234"

        # -- creation
        backoffice.users.create({"name": "bebert1", "surname": "bebert"})
        backoffice.users.create({"name": "bebert2", "surname": "bebert"})
        backoffice.users.create({"name": "bebert3", "surname": "Joe"})
        backoffice.users.create({"name": "bebert4", "surname": "Joe"})
        backoffice.users.create({"name": "bebert5", "surname": "Joe"})
        backoffice.users.create({"name": "bebert6", "surname": "Al"})
        backoffice.users.create({"name": "bebert7", "surname": "Al"})

        result = backoffice.users._selections["_all"].select({"surname": "Al"})
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["result"]), 2)
        for o in result["result"]:
            self.assertEqual(type(o), Item)
            self.assertEqual(o.surname, "Al")

        # check pagination
        result = backoffice.users._selections["_all"].select({"surname": "Al"}, 1, 0)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["result"]), 1)
        for o in result["result"]:
            self.assertEqual(type(o), Item)
            self.assertEqual(o.surname, "Al")

        # check not found
        result = backoffice.users._selections["_all"].select(
            {"surname_not_found": "Al"}
        )
        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["result"]), 0)
        result = backoffice.users._selections["_all"].select(
            {"surname": "Al_not_found"}
        )
        self.assertEqual(result["total"], 0)
        self.assertEqual(len(result["result"]), 0)
