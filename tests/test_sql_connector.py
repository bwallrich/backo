"""
test for CRUD()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import json

from backo import Item, Collection
from backo import DBSQLConnector
from backo import Backoffice, current_user

from backo import String, Bool, Int, Ref, RefsList, Dict  # , Error as StrictoError

from backo import log_system, LogLevel

### --- For development ---
log_system.add_handler(log_system.set_streamhandler())
log = log_system.get_or_create_logger("testing")
log_system.setLevel(LogLevel.DEBUG)


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
                "is_loved_by": RefsList(coll="animals", field="$.love"),
                "location": Dict({
                    "country": String(),
                    "city": String(),
                    "postal_code": Int()
                })
            }
        )

        animal_item = Item(
            {
                "surname": String(),
                "type": String(),
                "user": Ref(coll="users", field="$.animals", required=True),
                "love": RefsList(coll="users", field="$.is_loved_by"),
            }
        )

        self._meta = {}
        self._meta["users"] = user_item.get_schema()
        self._meta["animals"] = animal_item.get_schema()

        print(json.dumps(self._meta, indent=4))

        # --- DB for user
        self.db_users = DBSQLConnector(
            collection="users", path="sqlite_test_db", meta=self._meta
        )

        # --- DB for sites
        self.db_animals = DBSQLConnector(
            collection="animals", path="sqlite_test_db", meta=self._meta
        )

        print("3OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
        print(json.dumps(self.db_users._flatten_meta(self._meta), indent=4))

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

    # def test_db_connect(self):
    #     """
    #     try to connect
    #     """

    #     self.db_users.create_table()
    #     self.db_animals.create_table()
    #     self.db_users.drop()
    #     self.db_animals.drop()

    #     u0 = self._backoffice.users.create({"name": "bebert", "surname": "bebert"})
    #     u1 = self._backoffice.users.create({"name": "ted", "surname": "teddy"})
    #     u2 = self._backoffice.users.create(
    #         {"name": "benji", "surname": "benjie", "male": False}
    #     )

    #     # u0_ = backoffice.users.new()
    #     # u0_.load(u0._id)
    #     # print(u0_)
    #     # u1_ = backoffice.users.new()
    #     # u1_.load(u1._id)
    #     # print(u1_)
    #     # u2_ = backoffice.users.new()
    #     # u2_.load(u2._id)
    #     # print(u2_)

    #     a0 = self._backoffice.animals.create(
    #         {
    #             "surname": "cookie",
    #             "type": "dog",
    #             "user": u0._id,
    #             "love": [u0._id, u1._id, u2._id],
    #         }
    #     )
    #     a1 = self._backoffice.animals.create(
    #         {"surname": "pioo", "type": "bird", "user": u0._id, "love": [u0._id]}
    #     )

    #     u3 = self._backoffice.users.create(
    #         {"name": "jean", "surname": "valjean", "is_loved_by": [a1._id]}
    #     )

    #     print("RELOAD !!!!")
    #     # a1.reload()
    #     b = self._backoffice.animals.new()
    #     b.load(a1._id)

    #     print(a0.select("$.user.name"))
    #     print(a1.select("$.user.name"))

    #     print(f"{a0['surname']} loves ")
    #     print(a0.select("$.love.name"))

    #     print(f"{b['surname']} loves ")
    #     print(b.select("$.love.name"))
    #     print(f"{u3['surname']} is loved by ")
    #     print(f"{u3.select("$.is_loved_by.surname")}")

    #     # x_ = backoffice.users.new()
    #     # x_.load("plop")

    def test_one_to_many(self):
        pass

    def test_many_to_many(self):
        """
        Test many to many relationship
        """
        self.db_users.create_table()
        self.db_animals.create_table()
        self.db_users.drop()
        self.db_animals.drop()

        bebert = self._backoffice.users.create({"name": "bebert", "surname": "bebert"})
        jean = self._backoffice.users.create({"name": "jean", "surname": "valjean"})
        # ted = self._backoffice.users.create({"name": "ted", "surname": "teddy"})

        log.debug("# Create cookie")

        cookie = self._backoffice.animals.create(
            {
                "surname": "cookie",
                "type": "dog",
                "user": bebert._id,
                "love": [bebert._id, jean._id],
            }
        )

        # log.debug("# Create pioupiou")

        # pioupiou = self._backoffice.animals.create(
        #     {
        #         "surname": "pioupiou",
        #         "type": "bird",
        #         "user": ted._id,
        #         "love": [ted._id, jean._id],
        #     }
        # )

        log.debug("# Create benji")

        benji = self._backoffice.users.create(
            {
                "name": "benji",
                "surname": "benjie",
                "male": False,
                "is_loved_by": [cookie._id],
            }
        )

        self.assertEqual(len(cookie.love), 2)

        log.debug("# Reload cookie")

        cookie.reload()

        self.assertEqual(len(cookie.love), 3)
        self.assertEqual(len(benji.is_loved_by), 1)
