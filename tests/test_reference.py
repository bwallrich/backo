"""
test for References()
"""
# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import sys
sys.path.insert(1, "../stricto")

import unittest
import logging
from backo import GenericDB
from backo import DBYmlConnector
from backo import App
from backo import Ref, RefsList, DeleteStrategy, Error, log_system

### --- For development ---
log_system.add_handler( log_system.set_streamhandler() )
log = log_system.get_or_create_logger("testing")

from stricto import  String, Bool, Error as StrictoError


class TestReferences(unittest.TestCase):
    """
    DB with references ()
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        # --- DB for user
        self.yml_users = DBYmlConnector(path="/tmp")
        self.yml_users.generate_id = (
            lambda o: "User_" + o.name.get_value() + "_" + o.surname.get_value()
        )

        # --- DB for sites
        self.yml_sites = DBYmlConnector(path="/tmp")
        self.yml_sites.generate_id = lambda o: "Site_" + o.name.get_value()
        
        # --- DB for humans
        self.yml_humans = DBYmlConnector(path="/tmp")
        self.yml_humans.generate_id = lambda o: "Human_" + o.name.get_value()

        # --- DB for animals
        self.yml_animals = DBYmlConnector(path="/tmp")
        self.yml_animals.generate_id = lambda o: "Animal_" + o.desc.get_value()

    def test_references_one_to_many(self):
        """
        creating an app with ref one to many
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users", required=True),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users", field="$.site", ods=DeleteStrategy.MUST_BE_EMPTY
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.users.db.delete_by_id("User_bebert_bebert")

        si = app.sites.new()
        si.create({"name": "moon", "address": "far"})

        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert", "site": si._id})

        # -- Check if reverse is filled
        si.reload()
        self.assertEqual(len(si.users), 1)
        self.assertEqual(si.users[0], u._id)

        # -- check if deletion reverse is OK
        u.delete()
        si.reload()
        self.assertEqual(len(si.users), 0)

        # -- delete site
        si.delete()

    def test_references_one_to_many_strategy_clean(self):
        """
        creating an app with ref one to many
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users", field="$.site", ods=DeleteStrategy.CLEAN_REVERSES
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.users.db.delete_by_id("User_bebert_bebert")

        si = app.sites.new()
        si.create({"name": "moon", "address": "far"})

        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert", "site": si._id})

        # -- Check if reverse is filled
        si.reload()
        self.assertEqual(len(si.users), 1)
        self.assertEqual(si.users[0], u._id)

        # -- delete site
        si.delete()

        u.reload()
        self.assertEqual(u.site, None)

    def test_references_one_to_many_strategy_delete(self):
        """
        creating an app with ref one to many
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users",
                        field="$.site",
                        ods=DeleteStrategy.DELETE_REVERSES_TOO,
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.users.db.delete_by_id("User_bebert_bebert")

        si = app.sites.new()
        si.create({"name": "moon", "address": "far"})

        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert", "site": si._id})

        u.reload()
        self.assertEqual(u.site, si._id)


        # -- Check if reverse is filled
        si.reload()
        self.assertEqual(len(si.users), 1)
        self.assertEqual(si.users[0], u._id)


        # -- delete site
        si.delete()

        with self.assertRaises(Error) as e:
            u.reload()
        self.assertEqual(e.exception.message, '_id "User_bebert_bebert" not found')

    def test_references_errors(self):
        """
        creating an app with ref with errors
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users",
                        field="$.site",
                        ods=DeleteStrategy.DELETE_REVERSES_TOO,
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.users.db.delete_by_id("User_bebert_bebert")

        si = app.sites.new()
        si.create({"name": "moon", "address": "far"})

        u = app.users.new()
        self.assertEqual(u.site.get_root(), u)

        t_id = app.start_transaction()
        u.site._collection = "unknown_coll"
        with self.assertRaises(Error) as e:
            u.create({"name": "bebert", "surname": "bebert", "site": "1234"}, transaction_id=t_id)
        self.assertEqual(e.exception.message, 'Collection "unknown_coll" not found')
        app.rollback_transaction(t_id)

        t_id = app.start_transaction()
        # app.users.db.delete_by_id("User_bebert_bebert")
        u.site._collection = "sites"
        u.site._reverse = "unknown_reverse"
        with self.assertRaises(Error) as e:
            u.create({"name": "bebert", "surname": "bebert", "site": si._id}, transaction_id=t_id)
        self.assertEqual(
            e.exception.message, 'Collection "sites"."unknown_reverse" not found'
        )
        app.rollback_transaction(t_id)

        t_id = app.start_transaction()
        # app.users.db.delete_by_id("User_bebert_bebert")
        u.site._reverse = "users"
        with self.assertRaises(Error) as e:
            u.create({"name": "bebert", "surname": "bebert", "site": "no_ref"}, transaction_id=t_id)
        self.assertEqual(e.exception.message, '_id "no_ref" not found')
        app.rollback_transaction(t_id)

    def test_references_one_to_many_modification(self):
        """
        creating an app with ref one to many
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users",
                        field="$.site",
                        ods=DeleteStrategy.DELETE_REVERSES_TOO,
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.sites.db.delete_by_id("Site_mars")
        app.users.db.delete_by_id("User_bebert_bebert")

        si_mars = app.sites.new()
        si_mars.create({"name": "mars", "address": "very far"})

        si_moon = app.sites.new()
        si_moon.create({"name": "moon", "address": "far"})

        u = app.users.new()
        u.create({"name": "bebert", "surname": "bebert", "site": si_moon._id})

        # -- Check if reverse is filled
        si_moon.reload()
        self.assertEqual(len(si_moon.users), 1)
        self.assertEqual(si_moon.users[0], u._id)
        si_mars.reload()
        self.assertEqual(len(si_mars.users), 0)

        # -- change site
        u.site = si_mars._id
        u.save()

        # -- Check if reverse is modified
        si_moon.reload()
        self.assertEqual(len(si_moon.users), 0)

        si_mars.reload()
        self.assertEqual(len(si_mars.users), 1)
        self.assertEqual(si_mars.users[0], u._id)


    def test_references_many_to_one_modification(self):
        """
        creating an app with ref one to many
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "users",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "site": Ref(coll="sites", field="$.users"),
                    "male": Bool(default=True),
                },
                self.yml_users,
            ),
        )

        # --- DB for sites
        app.add_collection(
            "sites",
            GenericDB(
                {
                    "name": String(),
                    "address": String(),
                    "users": RefsList(
                        coll="users",
                        field="$.site",
                        ods=DeleteStrategy.CLEAN_REVERSES,
                    ),
                },
                self.yml_sites,
            ),
        )

        # Hard clean before tests
        app.sites.db.delete_by_id("Site_moon")
        app.sites.db.delete_by_id("Site_mars")
        app.users.db.delete_by_id("User_bebert_bebert")
        app.users.db.delete_by_id("User_john_john")

        si_mars = app.sites.new()
        si_mars.create({"name": "mars", "address": "very far"})

        si_moon = app.sites.new()
        si_moon.create({"name": "moon", "address": "far"})

        ub = app.users.new()
        ub.create({"name": "bebert", "surname": "bebert", "site": si_moon._id})

        uj = app.users.new()
        uj.create({"name": "john", "surname": "john", "site": si_moon._id})

        # -- Check if reverse is filled
        si_moon.reload()
        self.assertEqual(len(si_moon.users), 2)
        si_mars.reload()
        self.assertEqual(len(si_mars.users), 0)

        # -- Modify site
        si_mars.users = [ ub._id ]
        si_mars.save()
        si_mars = app.sites.new()
        si_mars.load("Site_mars")
        self.assertEqual(len(si_mars.users), 1)

        # -- Check if reverse is modified
        uj.reload()
        self.assertEqual(uj.site, si_moon._id )

        ub.reload()
        self.assertEqual(ub.site, si_mars._id )

        si_moon.reload()
        self.assertEqual(len(si_moon.users), 1)

    def test_references_one_to_one(self):
        """
        creating an app with ref one to one
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "humans",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "totem": Ref(coll="animals", field="$.human"),
                },
                self.yml_humans,
            ),
        )

        # --- DB for animal
        app.add_collection(
            "animals",
            GenericDB(
                {
                    "desc": String(),
                    "human": Ref(coll="humans", field="$.totem"),
                },
                self.yml_animals,
            ),
        )

        # Hard clean before tests
        app.humans.db.delete_by_id("Human_parker")
        app.humans.db.delete_by_id("Human_pym")
        app.animals.db.delete_by_id("Animal_spider")
        app.animals.db.delete_by_id("Animal_ant")

        # create humans
        up = app.humans.new()
        up.create({"name": "parker", "surname": "peter" })
        uh = app.humans.new()
        uh.create({"name": "pym", "surname": "hank" })

        # ctreate animal totem related to humans
        asp = app.animals.new()
        asp.create({"desc": "spider", "human" : up._id })
        aa = app.animals.new()
        aa.create({"desc": "ant", "human" : uh._id })

        # check human link
        up.reload()
        self.assertEqual(up.totem, asp._id )
        uh.reload()
        self.assertEqual(uh.totem, aa._id )

        # change the totem
        up.totem = aa._id
        up.save()

        aa.reload()
        self.assertEqual(aa.human, up._id )

        asp.reload()
        self.assertEqual(asp.human, None )

        uh.reload()
        self.assertEqual(uh.totem, None )

        # Delete
        aa.delete()
        up.reload()
        self.assertEqual(up.totem, None )


    def test_references_one_to_one_required(self):
        """
        creating an app with ref one to one with require
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "humans",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "totem": Ref(coll="animals", field="$.human", required=True),
                },
                self.yml_humans,
            ),
        )

        # --- DB for animal
        app.add_collection(
            "animals",
            GenericDB(
                {
                    "desc": String(),
                    "human": Ref(coll="humans", field="$.totem"),
                },
                self.yml_animals,
            ),
        )

        # Hard clean before tests
        app.humans.db.delete_by_id("Human_parker")
        app.humans.db.delete_by_id("Human_pym")
        app.animals.db.delete_by_id("Animal_spider")
        app.animals.db.delete_by_id("Animal_ant")

        # ctreate animal totem related to humans
        asp = app.animals.new()
        asp.create({"desc": "spider" })
        aa = app.animals.new()
        aa.create({"desc": "ant"})

        # create humans
        up = app.humans.new()
        up.create({"name": "parker", "surname": "peter", "totem" : asp._id })
        uh = app.humans.new()
        uh.create({"name": "pym", "surname": "hank", "totem" : aa._id })


        # check human link
        up.reload()
        self.assertEqual(up.totem, asp._id )
        uh.reload()
        self.assertEqual(uh.totem, aa._id )

        # take pym's totem. impossible (pym will have no totem)
        up.totem = aa._id
        with self.assertRaises(StrictoError) as e:
            up.save()
        self.assertEqual(e.exception.message, 'Cannot be empty')



    def test_references_many_to_many_empty_empty(self):
        """
        creating an app with many to many refs
        and delete
        """

        app = App("myApp")
        app.add_collection(
            "humans",
            GenericDB(
                {
                    "name": String(),
                    "surname": String(),
                    "totems": RefsList(coll="animals", field="$.humans", ods=DeleteStrategy.MUST_BE_EMPTY),
                },
                self.yml_humans,
            ),
        )

        # --- DB for animal
        app.add_collection(
            "animals",
            GenericDB(
                {
                    "desc": String(),
                    "humans": RefsList(coll="humans", field="$.totems", ods=DeleteStrategy.MUST_BE_EMPTY),
                },
                self.yml_animals,
            ),
        )

        # Hard clean before tests
        app.humans.db.delete_by_id("Human_parker")
        app.humans.db.delete_by_id("Human_pym")
        app.animals.db.delete_by_id("Animal_spider")
        app.animals.db.delete_by_id("Animal_ant")

        # ctreate animal totem related to humans
        asp = app.animals.new()
        asp.create({"desc": "spider" })
        aa = app.animals.new()
        aa.create({"desc": "ant"})

        # create humans
        up = app.humans.new()
        up.create({"name": "parker", "surname": "peter", "totems" : [asp._id, aa._id] })
        uh = app.humans.new()
        uh.create({"name": "pym", "surname": "hank", "totems" : [aa._id] })

        # check human links
        up.reload()
        self.assertEqual(len(up.totems), 2 )
        uh.reload()
        self.assertEqual(len(uh.totems), 1 )
        #check animals links
        asp.reload()
        self.assertEqual(len(asp.humans), 1 )
        aa.reload()
        self.assertEqual(len(aa.humans), 2 )

        # modify links
        asp.humans=[]
        asp.save()

        log.debug("----------------")

        up.reload()
        self.assertEqual(len(up.totems), 1 )
        up.totems.append(asp._id)
        up.save()
        asp.reload()
        self.assertEqual(len(asp.humans), 1 )
        
        # check if must be embty error
        with self.assertRaises(Error) as e:
            asp.delete()
        self.assertEqual(e.exception.message, 'Collection "humans" not empty')

