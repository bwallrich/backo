"""
test for CRUD()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest

# import json

from backo import Item, Collection
from backo import DBSQLiteConnector
from backo import Backoffice, current_user
from backo import NotFoundError

from backo import (
    String,
    Bool,
    Int,
    Float,
    Ref,
    RefsList,
    Dict,
)  # , Error as StrictoError

from backo import log_system, LogLevel

### --- For development ---
log_system.add_handler(log_system.set_streamhandler())
log = log_system.get_or_create_logger("testing")
log_system.setLevel(LogLevel.DEBUG)


class TestSQLiteConnector(unittest.TestCase):
    """
    DB SQLite crud
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
                # "totem": Ref(coll="animals", field="$.user"),
                "location": Dict(
                    {
                        "country": String(),
                        "city": String(),
                        "city_info": Dict(
                            {"postal_code": Int(), "gps_coord_x": Float()}
                        ),
                        "postal_code": Int(),
                    }
                ),
            }
        )

        animal_item = Item(
            {
                "surname": String(),
                "type": String(),
                "user": Ref(coll="users", field="$.animals", required=True),
                "love": RefsList(coll="users", field="$.is_loved_by"),
                # "totem_of": Ref(coll="humans", field="$.totem"),
            }
        )

        types_item = Item({"s": String(), "i": Int(), "b": Bool(), "f": Float()})

        self._meta = {}
        self._meta["users"] = user_item.get_schema()
        self._meta["animals"] = animal_item.get_schema()
        self._meta["types"] = types_item.get_schema()

        # print(json.dumps(self._meta, indent=4))

        # --- DB for user
        self.db_users = DBSQLiteConnector(
            collection="users", path="sqlite_test_db", meta=self._meta
        )

        # --- DB for animals
        self.db_animals = DBSQLiteConnector(
            collection="animals", path="sqlite_test_db", meta=self._meta
        )

        # --- DB for types
        self.db_types = DBSQLiteConnector(
            collection="types", path="sqlite_test_db", meta=self._meta
        )

        # print(json.dumps(self.db_users._flatten_meta(self._meta), indent=4))

        self._backoffice.register_collection(
            Collection(
                "types",
                types_item,
                self.db_types,
            )
        )

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

    def test_none_values(self):
        """
        Test CRUD on None values
        """
        self.db_types.create_table()
        self.db_types.drop()

        log.debug("Test None values")

        types = self._backoffice.types.create({"s": "hello"})

        loaded_types = self._backoffice.types.new()
        loaded_types.load(types._id)

        self.assertEqual(types.s, loaded_types.s)
        self.assertEqual(loaded_types.i, None)
        self.assertEqual(loaded_types.b, None)
        self.assertEqual(loaded_types.f, None)

    def test_types(self):
        """
        Test CRUD on different stricto types
        """
        self.db_types.create_table()
        self.db_types.drop()

        log.debug("Test support of object creation with different types")

        types = self._backoffice.types.create(
            {"s": "hello", "i": 42, "b": True, "f": 42.42}
        )

        types2 = self._backoffice.types.new()
        types2.load(types._id)

        self.assertEqual(types.s, types2.s)
        self.assertEqual(types.i, types2.i)
        self.assertEqual(types.b, types2.b)
        self.assertEqual(types.f, types2.f)

    def test_nested(self):
        """
        Test CRUD on nested fields
        """
        self.db_users.create_table()
        self.db_animals.create_table()
        self.db_types.create_table()

        self.db_users.drop()
        self.db_animals.drop()
        self.db_types.drop()

        log.debug("Test nested - one level")

        bebert = self._backoffice.users.create(
            {
                "name": "bebert",
                "surname": "bebert",
                "location": {"city": "pistache city", "country": "Pistachio"},
            }
        )

        bebert2 = self._backoffice.users.new()
        bebert2.load(bebert._id)

        self.assertEqual(bebert.location.city, bebert2.location.city)
        self.assertEqual(bebert.location.country, bebert2.location.country)

        log.debug("Test nested - n levels")

        joe = self._backoffice.users.create(
            {
                "name": "joe",
                "surname": "joe l'embrouille",
                "location": {"city_info": {"postal_code": 54, "gps_coord_x": 23.54345}},
            }
        )
        joe2 = self._backoffice.users.new()
        joe2.load(joe._id)

        self.assertEqual(joe.location.city_info.postal_code, 54)
        self.assertEqual(joe.location.city_info.gps_coord_x, 23.54345)

    def test_delete_by_id(self):
        """
        Test delete by id
        """
        self.db_users.create_table()
        self.db_animals.create_table()
        self.db_types.create_table()

        self.db_users.drop()
        self.db_animals.drop()
        self.db_types.drop()

        bebert = self._backoffice.users.create({"name": "bebert", "surname": "bebert"})
        bebert.delete()
        bebert2 = self._backoffice.users.new()

        self.assertRaises(NotFoundError, lambda: bebert2.load(bebert._id))

    def test_one_to_many(self):
        """
        Test one to many relationship
        """

        log.debug("# Clean up drop tables")

        self.db_users.drop_table()
        self.db_animals.drop_table()
        self.db_types.drop_table()

        log.debug("# Create tables")

        self.db_users.create_table()
        self.db_animals.create_table()
        self.db_types.create_table()

        bebert = self._backoffice.users.create({"name": "bebert", "surname": "bebert"})

        cookie = self._backoffice.animals.create(
            {
                "surname": "cookie",
                "type": "dog",
                "user": bebert._id,
                "love": [bebert._id],
            }
        )

        pioupiou = self._backoffice.animals.create(
            {
                "surname": "pioupiou",
                "type": "bird",
                "user": bebert._id,
                "love": [bebert._id],
            }
        )

        log.debug("# Reload bebert")
        bebert.reload()
        self.assertIn(pioupiou._id, bebert.animals)
        self.assertIn(cookie._id, bebert.animals)


    def test_many_to_many(self):
        """
        Test many to many relationship
        """
        self.db_users.create_table()
        self.db_animals.create_table()
        self.db_types.create_table()

        self.db_users.drop()
        self.db_animals.drop()
        self.db_types.drop()

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

    def test_nested_many_death_test(self):
        """Test of nested of nested of relation ship of the death metal !"""
