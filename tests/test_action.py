"""
test for Actions
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest


from backo import Item, Collection, Action
from backo import DBYmlConnector
from backo import Backoffice, Error

from stricto import String, Int, List

YML_DIR = "/tmp/backo_tests_actions"


class TestAction(unittest.TestCase):
    """
    DB sample crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        self.available = True
        self.can_execute = True

        # --- DB for user
        self.yml_users = DBYmlConnector(path=YML_DIR)
        self.yml_users.generate_id = (
            lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
        )
        self.yml_users.drop()

        # --- DB for sites
        self.yml_sites = DBYmlConnector(path=YML_DIR)
        self.yml_sites.generate_id = lambda o: "Site_" + o.name.get_value()

        self.yml_sites.drop()

    def is_available(self, right_name, action, o):  # pylint: disable=unused-argument
        """
        return available
        """
        return self.available

    def has_right_to_execute(
        self, right_name, action, o
    ):  # pylint: disable=unused-argument
        """
        return if can exec
        """
        return self.can_execute

    def test_sample_action(self):
        """
        create
        and delete errors
        """

        def increment(action, o):  # pylint: disable=unused-argument
            """
            Do the increment
            """
            o.comments.append(action.comment)
            o.stars += action.num

        def decrement(action, o):  # pylint: disable=unused-argument
            """
            Do the decrement
            """
            o.comments.append(action.comment)
            o.stars -= action.num

        backoffice = Backoffice("myApp")
        coll = Collection(
            "users",
            Item(
                {
                    "name": String(),
                    "surname": String(),
                    "comments": List(String(), default=[]),
                    "stars": Int(default=0),
                }
            ),
            self.yml_users,
        )
        backoffice.register_collection(coll)

        # Set the increment action
        incr = Action(
            {"comment": String(), "num": Int(default=0)},
            increment,
            can_see=self.is_available,
            can_execute=self.has_right_to_execute,
        )

        # Set the decrement action
        decr = Action({"comment": String(), "num": Int(default=0)}, decrement)

        # attach actions to a collection
        coll.register_action("increase", incr)
        coll.register_action("decrease", decr)

        self.yml_users.delete_by_id("User_bebert_bebert")

        v = backoffice.users.create({"name": "bebert", "surname": "bebert"})
        self.assertEqual(v.stars, 0)

        incr.set({"comment": "good boy", "num": 2})
        incr.go(v)

        self.assertEqual(v.stars, 2)
        self.assertEqual(len(v.comments), 1)
        self.assertEqual(v.comments[0], "good boy")
        decr.set({"comment": "bad boy", "num": 1})
        decr.go(v)
        self.assertEqual(v.stars, 1)
        self.assertEqual(len(v.comments), 2)
        self.assertEqual(v.comments[0], "good boy")
        self.assertEqual(v.comments[1], "bad boy")

        # check rights on actions
        self.available = False
        self.can_execute = True
        with self.assertRaises(Error) as e:
            incr.go(v)
        self.assertEqual(e.exception.message, "action increase not available")
        self.available = True
        self.can_execute = False
        with self.assertRaises(Error) as e:
            incr.go(v)
        self.assertEqual(e.exception.message, "action increase forbidden")
