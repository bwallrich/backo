"""
test for CRUD()
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest


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

        backoffice.register_collection(
            Collection(
                "users",
                Item(
                    {"name": String(), "surname": String(), "male": Bool(default=True)}
                ),
                self.db_users,
            )
        )

        # ignore sessions for this campaign of tests.
        current_user.standalone = True

        current_user.login = "Roger"
        current_user._id = "1234"

        # print(json.dumps(backoffice.users.get_meta(), indent=4))
        self.db_users.create_table(backoffice.users.get_meta())
        # self.db_users.drop()

        # u = backoffice.users.create({"name": "bebert", "surname": "bebert"})
        # print(u.name)
        # u.name = "bobi"
        # v = backoffice.users.new()
        # v.load(u._id)
