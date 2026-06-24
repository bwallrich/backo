"""Tests features of the DatabaseItem"""

import unittest
from unittest.mock import MagicMock, patch

from hamcrest import (
    assert_that,
    contains_exactly,
    has_properties,
)

from backo.database.item import DatabaseItem
from backo.database.attribute import DatabaseAttribute
from backo.database.mapper import ItemMapper


class TestDatabaseItem(unittest.TestCase):
    """Tests basics features of the DatabaseItem."""

    def test_init_database_item(self):
        """Tests the initialization process of the DatabaseItem.

        The path of each attribute in the model must be set on all attributes.
        """
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_mocks = [MagicMock(spec=DatabaseAttribute) for i in range(6)]

        DatabaseItem(
            item_mapper,
            {
                "name": attribute_mocks[0],
                "nested": {
                    "data": [
                        [attribute_mocks[1], attribute_mocks[2]],
                        attribute_mocks[3],
                        {"nested_data": attribute_mocks[4]},
                    ],
                    "time": attribute_mocks[5],
                },
            },
        )
        for attribute, path in zip(
            attribute_mocks,
            [
                ["name"],
                ["nested", "data", 0, 0],
                ["nested", "data", 0, 1],
                ["nested", "data", 1],
                ["nested", "data", 2, "nested_data"],
                ["nested", "time"],
            ],
        ):
            assert_that(
                attribute.set_attribute_path.call_args_list,
                contains_exactly(has_properties(args=contains_exactly(path))),
            )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_set_default_connection(self, connection):
        """Tests the set_default_connection methods sets the default connection
        of all attributes of the model.
        """
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, connection=None) for i in range(6)
        ]

        database_item = DatabaseItem(
            item_mapper,
            {
                "name": attribute_mocks[0],
                "nested": {
                    "data": [
                        [attribute_mocks[1], attribute_mocks[2]],
                        attribute_mocks[3],
                        {"nested_data": attribute_mocks[4]},
                    ],
                    "time": attribute_mocks[5],
                },
            },
        )

        database_item.set_default_connection(connection)

        for attribute in attribute_mocks:
            assert_that(
                attribute.set_default_connection.call_args_list,
                contains_exactly(has_properties(args=contains_exactly(connection))),
            )
