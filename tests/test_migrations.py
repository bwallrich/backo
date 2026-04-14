"""
test for References()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
from backo import Item, Collection
from backo import DBYmlConnector
from backo import Backoffice
from backo import current_user
from backo import (
    String,
    Bool,
    log_system,
    LogLevel,
    SSyntaxError,
    Int,
    SConstraintError,
    SAttributeError,
)

### --- For development ---
# import logging
# from backo import log_system
# log_system.setLevel(logging.DEBUG)
# log_system.add_handler(log_system.set_streamhandler())
# log = log_system.get_or_create_logger("testing")


YML_DIR = "/tmp/backo_tests_migrations"

log_migration = log_system.get_or_create_logger("migration")
log_migration.setLevel(LogLevel.DEBUG)


class TestMigrations(unittest.TestCase):
    """
    DB with references ()
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        # --- DB for user
        self.yml_users = DBYmlConnector(path=YML_DIR)
        self.yml_users.generate_id = (
            lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
        )

        self.backo = Backoffice("myApp")
        self.users = Collection(
            "users",
            Item(
                {
                    "name": String(),
                    "surname": String(),
                    "male": Bool(default=True),
                }
            ),
            self.yml_users,
        )

        self.backo.register_collection(self.users)

        self.yml_users.drop()
        current_user.standalone = True

        for x in range(10):
            self.backo.users.create(
                {"name": f"al{x}", "surname": f"al{x}", "male": True}
            )

    def test__migration_errors(self):
        """
        migration collection error
        """

        def migrate(o: dict) -> dict:
            """fake migration"""
            return o

        with self.assertRaises(SSyntaxError) as e:
            self.backo.migrate("unknown_collection", migrate)
        self.assertEqual(
            e.exception.to_string(),
            'Backoffice migration : collection "unknown_collection" not registered',
        )

    def test__migration_function_no_change(self):
        """
        migration function
        """

        report = self.backo.migrate("users")
        self.assertEqual(report.no_changes.total, 10)
        report = self.backo.migrate("users", _id="User_al0_al0")
        self.assertEqual(report.no_changes.total, 1)
        report = self.backo.migrate("users", _ids=["User_al0_al0", "User_al1_al1"])
        self.assertEqual(report.no_changes.total, 2)

    def test__migration_function_change(self):
        """
        migration function
        """

        def change_surname(o: dict):
            o["surname"] = o["surname"] + "_"
            return o

        report = self.backo.migrate("users", change_surname, _id="User_al0_al0")
        self.assertEqual(report.no_changes.total, 0)
        self.assertEqual(report.changes.total, 1)
        self.assertEqual(report.changes._ids[0], "User_al0_al0")

    def test_migration_alter_add_table(self):
        """
        migration function
        """

        def add_age(o: dict):
            o["age"] = 12
            return o

        def remove_age(o: dict):
            del o["age"]
            return o

        self.backo.users.model.add_to_model("age", Int(require=True))

        with self.assertRaises(SConstraintError) as e:
            self.backo.migrate("users", _id="User_al0_al0")
        self.assertEqual(e.exception.to_string(), '$.age: Cannot be empty "None"')
        report = self.backo.migrate("users", add_age, _id="User_al0_al0")
        self.assertEqual(report.no_changes.total, 0)
        self.assertEqual(report.changes.total, 1)
        self.assertEqual(report.changes._ids[0], "User_al0_al0")

        # do for real
        report = self.backo.migrate("users", add_age, dry_run=False)
        self.assertEqual(report.changes.total, 10)

        self.backo.users.model.remove_model("age")
        with self.assertRaises(SAttributeError) as e:
            self.backo.migrate("users", _id="User_al0_al0")
        self.assertEqual(e.exception.to_string(), '$: Unknown key "age"')
        report = self.backo.migrate("users", remove_age, dry_run=False)
        self.assertEqual(report.changes.total, 10)
