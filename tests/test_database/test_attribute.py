"""
Test module for backo.database.attribute.py
"""

import unittest
from unittest.mock import patch

from hamcrest import (
    assert_that,
    has_properties,
)


from backo.database.attribute import DatabaseAttribute


class TestDatabaseAttribute(unittest.TestCase):
    """Tests DatabaseAttribute"""

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_set_default_connection(self, connection):
        """Tests the default connection is set if no custom connection was
        provided to the DatabaseAttribute.
        """
        attribute = DatabaseAttribute()

        attribute.set_default_connection(connection)

        assert_that(attribute, has_properties(connection=connection))

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_set_default_connection_with_custom_connection(self, connection):
        """Tests the default connection is ignored is a custom connection was
        provided to the DatabaseAttribute.
        """
        custom_connection = connection()
        attribute = DatabaseAttribute(connection=custom_connection)

        attribute.set_default_connection(connection())

        assert_that(attribute, has_properties(connection=custom_connection))
