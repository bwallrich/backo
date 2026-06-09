"""
test for CRUD()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import json

from backo import Item, Collection
from backo import DBSQLConnector
from backo import Backoffice, current_user

from backo import String, Bool, Ref, RefsList  # , Error as StrictoError


class TestMongo(unittest.TestCase):
    """
    DB SQL crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        self._backoffice = Backoffice("myApp")

        user_item = Item(
            {
                "name": String(),
                "surname": String(),
                "male": Bool(default=True),
                "animals": RefsList(coll="animals", field="$.user"),
            }
        )

        animal_item = Item(
            {
                "surname": String(),
                "type": String(),
                "user": Ref(coll="users", field="$.animals", required=True),
            }
        )

        self._meta = {}
        self._meta["Users"] = user_item.get_schema()
        self._meta["Animals"] = animal_item.get_schema()
        self._user_meta = user_item.get_schema()
        self._animal_meta = animal_item.get_schema()

        print(json.dumps(self._user_meta, indent=4))
        print(json.dumps(self._animal_meta, indent=4))

        # --- DB for user
        self.db_users = DBSQLConnector(collection="Users", path="sqlite_test_db", meta=self._user_meta)

        # --- DB for sites
        self.db_animals = DBSQLConnector(collection="Animals", path="sqlite_test_db", meta=self._animal_meta)

        self._backoffice.register_collection(
            Collection(
                "users",
                user_item,
                self.db_users,
            )
        )

        self._backoffice.register_collection(
            Collection(
                "animals",
                animal_item,
                self.db_animals,
            )
        )

        # ignore sessions for this campaign of tests.
        current_user.standalone = True

        current_user.login = "Roger"
        current_user._id = "1234"

    def tearDown(self):
        self.db_animals.close()
        self.db_users.close()
        return super().tearDown()

    def test_db_connect(self):
        """
        try to connect
        """




        self.db_users.create_table()
        self.db_animals.create_table()
        self.db_users.drop()
        self.db_animals.drop()

        u0 = self._backoffice.users.create({"name": "bebert", "surname": "bebert"})
        u1 = self._backoffice.users.create({"name": "ted", "surname": "teddy"})
        u2 = self._backoffice.users.create(
            {"name": "benji", "surname": "benjie", "male": False}
        )

        # u0_ = backoffice.users.new()
        # u0_.load(u0._id)
        # print(u0_)
        # u1_ = backoffice.users.new()
        # u1_.load(u1._id)
        # print(u1_)
        # u2_ = backoffice.users.new()
        # u2_.load(u2._id)
        # print(u2_)

        a0 = self._backoffice.animals.create({"surname": "cookie", "type": "dog", "user": u0._id})
        a1 = self._backoffice.animals.create({"surname": "pioo", "type": "bird", "user": u0._id})

        
        print(a0.select("$.user.name"))

        # x_ = backoffice.users.new()
        # x_.load("plop")
