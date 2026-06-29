"""DatabaseItem search operation tests"""

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


class TestDatabaseItemSelect(unittest.TestCase):
    """Tests select requests building depending on the complexity of the model."""

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_select_request_single_attribute_model(self, connection):
        """Tests the validity of built search requests for a single attribute model."""
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.select_request.return_value = base_request

        attribute_request = MagicMock(connection=None)
        attribute_mock = MagicMock(
            spec=DatabaseAttribute,
            request=attribute_request,
            connection=connection,
        )

        attribute_mock.select_request.return_value = attribute_request

        database_item = DatabaseItem(item_mapper, attribute_mock)
        # Connection used for the base request
        database_item.connection = connection

        item_filter = ("$eq", "mock_id")
        select_requests = database_item.select_request(item_filter)

        # As a side effect, the connection must have been set up on all requests
        # returned in select_requests
        assert_that(base_request, has_properties(connection=connection))
        assert_that(attribute_request, has_properties(connection=connection))

        assert_that(
            item_mapper.select_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(item_filter))),
        )
        assert_that(
            attribute_mock.select_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        item_mapper.select_request.return_value, item_filter
                    )
                )
            ),
        )

        assert_that(
            select_requests,
            contains_exactly(
                item_mapper.select_request.return_value, attribute_request
            ),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_select_request_with_none_request(self, connection):
        """Tests the validity of built select requests for a single attribute
        model that return no request."""
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.select_request.return_value = base_request

        attribute_mock = MagicMock(
            spec=DatabaseAttribute,
            connection=connection,
        )

        attribute_mock.select_request.return_value = None

        database_item = DatabaseItem(item_mapper, attribute_mock)
        # Connection used for the base request
        database_item.connection = connection

        item_filter = ("$eq", "mock_id")
        select_requests = database_item.select_request(item_filter)

        # As a side effect, the connection must have been set up on all requests
        # returned in select_requests
        assert_that(base_request, has_properties(connection=connection))

        assert_that(
            item_mapper.select_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(item_filter))),
        )
        assert_that(
            attribute_mock.select_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        item_mapper.select_request.return_value, item_filter
                    )
                )
            ),
        )

        assert_that(
            select_requests,
            contains_exactly(item_mapper.select_request.return_value, None),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_select_request_simple_list_model(self, connection):
        """Tests the validity of built select requests for a list model."""
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.select_request.return_value = base_request

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
            attribute_mocks[i].select_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(
            item_mapper,
            attribute_mocks,
        )
        # Connection used for the base request
        database_item.connection = connection

        item_filter = [("$eq", "data"), ("$gt", 12), ("$any")]
        select_requests = database_item.select_request(item_filter)

        # As a side effect, the connection must have been set up on all requests
        # returned in select_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.select_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(item_filter))),
        )
        for attribute, attribute_filter in zip(attribute_mocks, item_filter):
            assert_that(
                attribute.select_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.select_request.return_value, attribute_filter
                        )
                    )
                ),
            )

        assert_that(
            select_requests,
            contains_exactly(
                item_mapper.select_request.return_value,
                contains_exactly(*attribute_requests),
            ),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_select_request_simple_dict_model(self, connection):
        """Tests the validity of built select requests for a dict model."""
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.select_request.return_value = base_request

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
            attribute_mocks[i].select_request.return_value = attribute_requests[i]

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

        item_filter = {
            # No need to specify a filter for each field
            "login": ("$eq", "mock_login"),
            "name": ("$reg", "mock.*"),
        }
        select_requests = database_item.select_request(item_filter)

        # As a side effect, the connection must have been set up on all requests
        # returned in select_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.select_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(item_filter))),
        )
        for attribute, attribute_filter in zip(
            attribute_mocks[:2],
            [
                ("$eq", "mock_login"),
                ("$reg", "mock.*"),
            ],
        ):
            assert_that(
                attribute.select_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.select_request.return_value, attribute_filter
                        )
                    )
                ),
            )

        assert_that(
            select_requests,
            contains_exactly(
                item_mapper.select_request.return_value,
                has_entries(
                    {
                        "login": attribute_requests[0],
                        "name": attribute_requests[1],
                    }
                ),
            ),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_select_request_with_complex_nested_attributes(self, connection):
        """Tests the validity of built select requests for a model with
        attributes nested in dicts and lists.
        """
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.select_request.return_value = base_request

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
            attribute_mocks[i].select_request.return_value = attribute_requests[i]

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

        item_filter = {
            "nested": {
                "data": [
                    [("$eq", 13), ("$eq", 12)],
                    ("$reg", r"\S*"),
                    {},
                ],
                "time": ("$lt", 2027),
            },
        }

        select_requests = database_item.select_request(item_filter)

        # As a side effect, the connection must have been set up on all requests
        # returned in select_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.select_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(item_filter))),
        )
        for attribute, attribute_filter in zip(
            attribute_mocks,
            [None, ("$eq", 13), ("$eq", 12), ("$reg", r"\S*"), None, ("$lt", 2027)],
        ):
            assert_that(
                attribute.select_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.select_request.return_value, attribute_filter
                        )
                    )
                ),
            )

        assert_that(
            select_requests,
            contains_exactly(
                item_mapper.select_request.return_value,
                has_entries(
                    {
                        "name": attribute_requests[0],
                        "nested": has_entries(
                            {
                                "data": contains_exactly(
                                    contains_exactly(
                                        attribute_requests[1], attribute_requests[2]
                                    ),
                                    attribute_requests[3],
                                    has_entries({"nested_data": attribute_requests[4]}),
                                ),
                                "time": attribute_requests[5],
                            }
                        ),
                    }
                ),
            ),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_select_multiple_request_attribute(self, connection):
        """Tests the validity of built select requests for a model with
        attributes that require multiple requests nested in dicts and lists.
        """
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.select_request.return_value = base_request

        attribute_requests = [MagicMock() for _ in range(5)]
        attribute_mocks = [
            MagicMock(
                spec=DatabaseAttribute,
                request=attribute_requests[i],
                connection=connection,
            )
            for i in range(2)
        ]
        attribute_mocks[0].select_request.return_value = {
            "request1": attribute_requests[0],
            "request2": attribute_requests[1],
        }
        attribute_mocks[1].select_request.return_value = [
            attribute_requests[2],
            {"req1": attribute_requests[3], "req2": attribute_requests[4]},
        ]

        database_item = DatabaseItem(
            item_mapper,
            {"foo": attribute_mocks[0], "nested": {"bar": attribute_mocks[1]}},
        )
        # Connection used for the base request
        database_item.connection = connection

        select_item = {"foo": ("$eq", "value"), "nested": {"bar": ("$gt", 13)}}
        select_requests = database_item.select_request(select_item)

        # As a side effect, the connection must have been set up on all requests
        # returned in select_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.select_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(select_item))),
        )
        for attribute, attribute_filter in zip(
            attribute_mocks, [("$eq", "value"), ("$gt", 13)]
        ):
            assert_that(
                attribute.select_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.select_request.return_value, attribute_filter
                        )
                    )
                ),
            )

        assert_that(
            select_requests,
            contains_exactly(
                item_mapper.select_request.return_value,
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
