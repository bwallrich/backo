"""
test for References()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest
from backo import Item, Collection, View
from backo import DBYmlConnector
from backo import Backoffice
from backo import Ref, RefsList, DeleteStrategy

### --- For development ---
# log_system.add_handler(log_system.set_streamhandler())
# log = log_system.get_or_create_logger("testing")

from stricto import String, Bool

YML_DIR = "/tmp/backo_tests_views"


class TestViews(unittest.TestCase):
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

    def test_ref_view(self):
        """
        creating an backoffice with ref one to many
        and use selectors to cross
        """

        # Hard clean before tests
        self.yml_sites.delete_by_id("Site_moon")
        self.yml_sites.delete_by_id("Site_mars")
        self.yml_users.delete_by_id("User_bebert_bebert")
        self.yml_users.delete_by_id("User_john_john")

        v = View("males", self.users, ["$.name", "$.male"])
        # vv = View( 'localisation', self.users, [ '$.name', '$.site.address' ])

        # si_moon = self.sites.create({"name": "moon", "address": "far"})

        u = v.get_by_id("User_john_john")
        self.assertEqual(u.get_value(), {"name": "john", "male": True})
        # u = vv.get_by_id( 'User_john_john' )
        # self.assertEqual(u.get_value(), {} )
