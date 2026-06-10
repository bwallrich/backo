"""
test for api toolbkx
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest


from werkzeug.datastructures import ImmutableMultiDict
from backo import multidict_to_filter, append_path_to_filter, flatter, unflatter


class TestApiToolbox(unittest.TestCase):
    """
    API toolbox tests
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

    def test_sub(self):
        """
        test sub
        """
        md = ImmutableMultiDict(
            [("a", "1"), ("toto", "1"), ("toto", "2"), ("b.c", "in"), ("b.d", "out")]
        )
        my_filter = multidict_to_filter(md)
        self.assertEqual(my_filter["a"], 1)
        self.assertNotEqual(my_filter["a"], "1")
        self.assertNotEqual(my_filter["toto"], ["1", "2"])
        self.assertEqual(my_filter["toto"], [1, 2])
        self.assertEqual(my_filter["b"]["c"], "in")
        self.assertEqual(my_filter["b"]["d"], "out")

    def test_sub_error(self):
        """
        test sub
        """
        md = ImmutableMultiDict([("a", "1"), ("b.c", "in"), ("b", "23")])
        my_filter = multidict_to_filter(md)
        self.assertEqual(my_filter["a"], 1)
        self.assertEqual(my_filter["b"], 23)

    def test_operators(self):
        """
        test_operators
        """
        md = ImmutableMultiDict([("a", "1"), ("toto.$gt", "1"), ("b.c.$re", "in")])
        my_filter = multidict_to_filter(md)
        self.assertEqual(my_filter["a"], 1)
        self.assertEqual(my_filter["toto"], ("$gt", 1))
        self.assertEqual(my_filter["b"]["c"], ("$re", "in"))

    def test_append_path_to_filter(self):
        """
        test_append_path_to_filter
        """
        o = {}
        append_path_to_filter(o, "name", "zaza")
        self.assertEqual(o["name"], "zaza")
        append_path_to_filter(o, "sub.aa", "zaza")
        self.assertEqual(o["sub"]["aa"], "zaza")
        append_path_to_filter(o, "sub.bb", "zozo")
        self.assertEqual(o["sub"]["bb"], "zozo")
        append_path_to_filter(o, "sec", ["sec_0"])

    def test_flat(self):
        """
        test_append_path_to_filter
        """
        o = {
            "name": "a",
            "loc": {"a": 1, "b": 2},
            "c": [1, 2],
            "d": [{"i": 1, "j": {"k": 2}}, {"i": 11, "j": {"k": 22}}],
        }
        f = {}
        flatter(f, o)
        self.assertEqual(
            str(f),
            "{'name': 'a', 'loc.a': 1, 'loc.b': 2, 'c': [1, 2], 'd': [{'i': 1, 'j.k': 2}, {'i': 11, 'j.k': 22}]}",
        )

    def test_unflat(self):
        """
        test_append_path_to_filter
        """
        o = {
            "name": "a",
            "loc.a": 1,
            "loc.b": 2,
            "c": [1, 2],
            "d": [{"i": 1, "j.k": 2}, {"i": 11, "j.k": 22}],
        }
        f = {}
        for k, v in o.items():
            unflatter(f, k.split("."), v)
        self.assertEqual(
            str(f),
            "{'name': 'a', 'loc': {'b': 2}, 'c': [1, 2], 'j.k': [{'i': 1, 'j': {'k': 2}}, {'i': 11, 'j': {'k': 22}}]}",
        )
