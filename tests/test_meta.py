"""
test for Meta data
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
import pprint

pp = pprint.PrettyPrinter(indent=2)


from backo import Item, Collection
from backo import DBYmlConnector
from backo import Backoffice
from backo import Ref, RefsList, DeleteStrategy

### --- For development ---
# log_system.add_handler(log_system.set_streamhandler())
# log = log_system.get_or_create_logger("testing")

from stricto import String, Bool

YML_DIR = "/tmp/backo_tests_meta"


class TestMeta(unittest.TestCase):
    """
    DB with a reference ()
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

        # --- DB for sites
        self.yml_sites = DBYmlConnector(path=YML_DIR)
        self.yml_sites.generate_id = lambda o: "Site_" + o.name.get_value()

        self.backoffice = Backoffice("myApp")
        self.users = Collection(
            "users",
            Item(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                }
            ),
            self.yml_users,
        )
        self.sites = Collection(
            "sites",
            Item(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users",
                        field="$.site",
                        ods=DeleteStrategy.UNLINK_REFERENCED_ITEMS,
                    ),
                }
            ),
            self.yml_sites,
        )
        self.backoffice.register_collection(self.users)
        self.backoffice.register_collection(self.sites)

        self.yml_users.drop()
        self.yml_sites.drop()

        s = self.backoffice.sites.create({"name": "earth", "address": "here"})

        self.backoffice.users.create(
            {"name": "bebert", "surname": "bebert", "site": s._id}
        )
        self.backoffice.users.create(
            {"name": "bert1", "surname": "bert1", "site": s._id}
        )
        self.backoffice.users.create(
            {"name": "bert2", "surname": "bert2", "site": s._id}
        )

        s = self.backoffice.sites.create({"name": "moon", "address": "not so far"})

        self.backoffice.users.create(
            {"name": "bert3", "surname": "bert3", "site": s._id}
        )

        s = self.backoffice.sites.create({"name": "mars", "address": "far"})
        s = self.backoffice.sites.create({"name": "jupiter", "address": "bad idea"})

    def test_get_meta(self):
        """
        get meta informations
        """
        d = self.backoffice.get_meta()
        self.assertEqual(list(d.keys()), ["name", "collections"])
        for collection in d["collections"]:
            self.assertEqual("item" in collection.keys(), True)
            schema = collection["item"]
            self.assertEqual("type" in schema, True)

    def test_get_current_meta(self):
        """
        get meta informations
        """

        s = self.backoffice.sites.create({"name": "saturn", "address": "farfar"})
        u = self.backoffice.users.create(
            {"name": "vador", "surname": "dark", "site": s._id}
        )

        meta = u.get_current_meta()
        self.assertEqual(meta["exists"], True)
        self.assertEqual(meta["rights"]["read"], True)
        self.assertEqual(meta["rights"]["modify"], True)
