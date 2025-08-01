"""
test for api toolbkx
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import unittest


from werkzeug.datastructures import ImmutableMultiDict
from backo import multidict_to_filter


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
