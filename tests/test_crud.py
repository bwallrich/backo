"""
test for CRUD()
"""
# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import sys

sys.path.insert(1, "../../stricto")


import unittest
import time


from backo import Item, Collection
from backo import DBYmlConnector
from backo import App, Error, current_user

from stricto import String, Bool, Error as StrictoError


class TestCRUD(unittest.TestCase):
    """
    DB sample crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        # --- DB for user
        self.yml_users = DBYmlConnector(path="/tmp/backo")
        self.yml_users.generate_id = (
            lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
        )

        # --- DB for sites
        self.yml_sites = DBYmlConnector(path="/tmp/backo")
        self.yml_sites.generate_id = lambda o: "Site_" + o.name.get_value()

    def test_errors_on_create_delete(self):
        """
        create
        and delete errors
        """

        app = App("myApp")
        
        app.register_collection(
            Collection(
                'users', 
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)}
                ),
                self.yml_users)
        )

        self.yml_users.delete_by_id("User_bebert_bebert")

        v = app.users.new()
        with self.assertRaises(Error) as e:
            v.delete()
        self.assertEqual(e.exception.message, "Cannot delete an unset object in users")
        with self.assertRaises(Error) as e:
            v.save()
        self.assertEqual(e.exception.message, "Cannot save an unset object in users")
        v.create({"name": "bebert", "surname": "bebert"})
        with self.assertRaises(Error) as e:
            v.load("test")
        self.assertEqual(
            e.exception.message, "Cannot load an non-unset object in users"
        )

    def test_create_delete(self):
        """
        create
        and delete
        """

        app = App("myApp")
        
        app.register_collection(
            Collection(
                'users', 
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)}
                ),
                self.yml_users)
        )

        self.yml_users.delete_by_id("User_bebert_bebert")

        current_user.login = "Roger"
        current_user.user_id = "1234"

        # -- creation
        u = app.users.create({"name": "bebert", "surname": "bebert"})
        v = app.users.new()
        v.load(u._id.get_value())
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
        v.load(u._id.get_value())
        self.assertEqual(v.male, False)
        self.assertEqual(v._meta.mtime > v._meta.ctime, True)
        self.assertEqual(v._meta.created_by.login, "Roger")
        self.assertEqual(v._meta.created_by.user_id, "1234")
        self.assertEqual(v._meta.modified_by.login, "Mary")
        self.assertEqual(v._meta.modified_by.user_id, "4321")

        # -- delete
        u.delete()
        v = app.users.new()
        with self.assertRaises(Error) as e:
            v.load("User_bebert_bebert")
        self.assertEqual(e.exception.message, '_id "User_bebert_bebert" not found')

    def test_create_ids(self):
        """
        create
        and delete
        """

        app = App("myApp")
        
        app.register_collection(
            Collection(
                'users', 
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)}
                ),
                self.yml_users)
        )

        self.yml_users.delete_by_id("User_bebert_bebert")

        # -- creation
        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert"})
        self.assertEqual(u._id, "User_bebert_bebert")
        u.surname = "foo"
        u.save()

        v = app.users.new()
        v.load(u._id.get_value())
        self.assertEqual(v.surname, "foo")

        with self.assertRaises(StrictoError) as e:
            v._meta.ctime = 12
        self.assertEqual(e.exception.message, "cannot modify value")

    def test_crud_no_meta(self):
        """
        create
        and delete
        """

        app = App("myApp")
        
        app.register_collection(
            Collection(
                'users', 
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)},
                    meta_data_handler = None
                ),
                self.yml_users)
        )

        self.yml_users.delete_by_id("User_bebert_bebert")

        # -- creation
        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert"})
        self.assertEqual(u._id, "User_bebert_bebert")
        u.surname = "foo"
        u.save()

        v = app.users.new()
        v.load(u._id.get_value())
        self.assertEqual(v.surname, "foo")

        with self.assertRaises(AttributeError) as e:
            print(v._meta)
        self.assertEqual(e.exception.args[0], "'Item' object has no attribute '_meta'")
