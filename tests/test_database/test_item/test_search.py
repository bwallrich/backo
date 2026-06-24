"""DatabaseItem search operation tests
"""

import unittest
from unittest.mock import MagicMock, patch

from hamcrest import (
    assert_that,
    contains_exactly,
    has_entries,
    has_properties,
)

from backo.database.item import DatabaseItem
from backo.database.attribute import DatabaseAttribute
from backo.database.mapper import ItemMapper


class TestDatabaseItemSearch(unittest.TestCase):
    """Tests search requests building depending on the complexity of the model."""

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_search_request_simple_item(self, connection):
        """Tests the validity of built search requests for a model without
        nested attributes.
        """
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.search_request.return_value = base_request

        attribute_requests = [MagicMock(connection=None) for _ in range(3)]
        attribute_mocks = [
            MagicMock(
                spec=DatabaseAttribute,
                request=attribute_requests[i],
                connection=connection,
            )
            for i in range(3)
        ]
        for i in range(3):
            attribute_mocks[i].search_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(
            item_mapper,
            {
                "login": attribute_mocks[0],
                "name": attribute_mocks[1],
                "contact": attribute_mocks[2],
            },
        )
        # Connection used for the base request
        database_item.connection = connection

        search_requests = database_item.search_request("mock_id")

        # As a side effect, the connection must have been set up on all requests
        # returned in search_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.search_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )
        for attribute in attribute_mocks:
            assert_that(
                attribute.search_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.search_request.return_value, "mock_id"
                        )
                    )
                ),
            )

        assert_that(
            search_requests,
            contains_exactly(
                item_mapper.search_request.return_value,
                has_entries(
                    {
                        "login": attribute_requests[0],
                        "name": attribute_requests[1],
                        "contact": attribute_requests[2],
                    }
                ),
            ),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_search_request_with_complex_nested_attributes(self, connection):
        """Tests the validity of built search requests for a model with
        attributes nested in dicts and lists.
        """
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.search_request.return_value = base_request

        attribute_requests = [MagicMock() for _ in range(6)]
        attribute_mocks = [
            MagicMock(
                spec=DatabaseAttribute,
                request=attribute_requests[i],
                connection=connection,
            )
            for i in range(6)
        ]
        for i in range(6):
            attribute_mocks[i].search_request.return_value = attribute_requests[i]

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
        # Connection used for the base request
        database_item.connection = connection

        search_requests = database_item.search_request("mock_id")

        # As a side effect, the connection must have been set up on all requests
        # returned in search_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.search_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )
        for attribute in attribute_mocks:
            assert_that(
                attribute.search_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.search_request.return_value, "mock_id"
                        )
                    )
                ),
            )

        assert_that(
            search_requests,
            contains_exactly(
                item_mapper.search_request.return_value,
                has_entries(
                    {
                        "name": attribute_requests[0],
                        "nested": {
                            "data": [
                                [attribute_requests[1], attribute_requests[2]],
                                attribute_requests[3],
                                {"nested_data": attribute_requests[4]},
                            ],
                            "time": attribute_requests[5],
                        },
                    }
                ),
            ),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_search_multiple_request_attribute(self, connection):
        """Tests the validity of built search requests for a model with
        attributes that require multiple requests nested in dicts and lists.
        """
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.search_request.return_value = base_request

        attribute_requests = [MagicMock() for _ in range(5)]
        attribute_mocks = [
            MagicMock(
                spec=DatabaseAttribute,
                request=attribute_requests[i],
                connection=connection,
            )
            for i in range(2)
        ]
        attribute_mocks[0].search_request.return_value = {
            "request1": attribute_requests[0],
            "request2": attribute_requests[1],
        }
        attribute_mocks[1].search_request.return_value = [
            attribute_requests[2],
            {"req1": attribute_requests[3], "req2": attribute_requests[4]},
        ]

        database_item = DatabaseItem(
            item_mapper,
            {"foo": attribute_mocks[0], "nested": {"bar": attribute_mocks[1]}},
        )
        # Connection used for the base request
        database_item.connection = connection

        search_requests = database_item.search_request("mock_id")

        # As a side effect, the connection must have been set up on all requests
        # returned in search_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.search_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )
        for attribute in attribute_mocks:
            assert_that(
                attribute.search_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.search_request.return_value, "mock_id"
                        )
                    )
                ),
            )

        assert_that(
            search_requests,
            contains_exactly(
                item_mapper.search_request.return_value,
                has_entries(
                    {
                        "foo": has_entries(
                            {
                                "request1": attribute_requests[0],
                                "request2": attribute_requests[1],
                            }
                        ),
                        "nested": has_entries(
                            {
                                "bar": contains_exactly(
                                    attribute_requests[2],
                                    has_entries(
                                        {
                                            "req1": attribute_requests[3],
                                            "req2": attribute_requests[4],
                                        }
                                    ),
                                )
                            }
                        ),
                    }
                ),
            ),
        )
