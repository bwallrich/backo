"""
test for Actions
"""
# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import sys

sys.path.insert(1, "../../stricto")


import unittest
import time


from backo import Item, Collection, Action
from backo import DBYmlConnector
from backo import App, Error, current_user

from stricto import String, Int, List, Error as StrictoError


class TestAction(unittest.TestCase):
    """
    DB sample crud
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        self.doable = True
        self.exec = True

        # --- DB for user
        self.yml_users = DBYmlConnector(path="/tmp")
        self.yml_users.generate_id = (
            lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
        )

        # --- DB for sites
        self.yml_sites = DBYmlConnector(path="/tmp")
        self.yml_sites.generate_id = lambda o: "Site_" + o.name.get_value()


    def is_doable(self, app, collection, action, o):
        """
        return doable
        """
        return self.doable

    def is_exec(self, app, collection, action, o):
        """
        return if can exect
        """
        return self.exec

    def test_sample_action(self):
        """
        create
        and delete errors
        """

        def increment(app, collection, action, o ):
            """
            Do the increment
            """
            o.comments.append(action.comment)
            o.stars +=action.num
            
        def decrement(app, collection, action, o ):
            """
            Do the decrement
            """
            o.comments.append(action.comment)
            o.stars -=action.num

        def doable(app, collection, action, o ):
            """
            return True of False
            """
            

        app = App("myApp")
        coll = Collection(
                'users', 
                Item({
                     "name": String(),
                     "surname": String(),
                     "comments" : List( String(), default=[] ),
                     "stars": Int(default=0)
                }),
                self.yml_users)
        app.register_collection( coll )

        # Set the increment action
        incr  = Action({
            "comment" : String(),
            "num" : Int(default=0)
        }, increment, doable=self.is_doable, exec=self.is_exec )

        # Set the decrement action
        decr  = Action({
            "comment" : String(),
            "num" : Int(default=0)
        }, decrement )

        # attach actions to a collection 
        coll.register_action("increase", incr )
        coll.register_action("decrease", decr )


        self.yml_users.delete_by_id("User_bebert_bebert")

        v = app.users.create({"name": "bebert", "surname": "bebert"})
        self.assertEqual(v.stars, 0)


        incr.set({
            "comment" : "good boy",
            "num" : 2
        })
        incr.go( v )


        self.assertEqual(v.stars, 2)
        self.assertEqual(len(v.comments), 1)
        self.assertEqual(v.comments[0], "good boy")
        decr.set({
            "comment" : "bad boy",
            "num" : 1
        })
        decr.go( v )
        self.assertEqual(v.stars, 1)
        self.assertEqual(len(v.comments), 2)
        self.assertEqual(v.comments[0], "good boy")
        self.assertEqual(v.comments[1], "bad boy")

        # check rights on actions
        self.doable = False
        with self.assertRaises(Error) as e:
            incr.go( v )
        self.assertEqual(e.exception.message, "action increase not available")
        self.doable = True
        self.exec = False
        with self.assertRaises(Error) as e:
            incr.go( v )
        self.assertEqual(e.exception.message, "action increase forbidden")
