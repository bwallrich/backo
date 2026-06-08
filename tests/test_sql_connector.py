"""
test for CRUD()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import json

from backo import Item, Collection
from backo import DBSQLConnector
from backo import Backoffice, current_user

from backo import String, Bool  # , Error as StrictoError


class TestMongo(unittest.TestCase):
    """
    DB SQL crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        # --- DB for user
        self.db_users = DBSQLConnector(collection="Users", path="sqlite_test_db")

        # --- DB for sites
        self.db_site = DBSQLConnector(collection="Sites", path="sqlite_test_db")

    def tearDown(self):
        self.db_site.close()
        self.db_users.close()
        return super().tearDown()

    def test_db_connect(self):
        """
        try to connect
        """

        backoffice = Backoffice("myApp")
        user_item = Item(
            {"name": String(), "surname": String(), "male": Bool(default=True)}
        )

        meta = user_item.get_schema()
        print(meta)

        backoffice.register_collection(
            Collection(
                "users",
                user_item,
                self.db_users,
            )
        )

        # ignore sessions for this campaign of tests.
        current_user.standalone = True

        current_user.login = "Roger"
        current_user._id = "1234"

        print(json.dumps(meta, indent=4))
        self.db_users.create_table(meta)
        self.db_users.drop()

        u = backoffice.users.create({"name": "bebert", "surname": "bebert"})
        v = backoffice.users.create({"name": "ted", "surname": "teddy"})
        w = backoffice.users.create(
            {"name": "benji", "surname": "benjie", "male": False}
        )
        # print(u.name)
        # u.name = "bobi"
        u_ = backoffice.users.new()
        u_.load(u._id)
        print(u_)
        v_ = backoffice.users.new()
        v_.load(v._id)
        print(v_)
        w_ = backoffice.users.new()
        w_.load(w._id)
        print(w_)
