"""DatabaseItem update operation tests"""

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


class TestDatabaseItemUpdate(unittest.TestCase):
    """Tests update requests building depending on the complexity of the model."""

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_update_request_single_attribute_model(self, connection):
        """Tests the validity of built update requests for a single attribute model."""
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.update_request.return_value = base_request

        attribute_request = MagicMock(connection=connection)
        attribute_mock = MagicMock(
            spec=DatabaseAttribute,
            request=attribute_request,
            connection=connection,
        )
        attribute_mock.update_request.return_value = attribute_request

        database_item = DatabaseItem(item_mapper, attribute_mock)
        # Connection used for the base request
        database_item.connection = connection

        update_requests = database_item.update_request("mock_id", "new_value")

        # As a side effect, the connection must have been set up on all requests
        # returned in search_requests
        assert_that(base_request, has_properties(connection=connection))
        assert_that(attribute_request, has_properties(connection=connection))

        assert_that(
            item_mapper.update_request.call_args_list,
            contains_exactly(
                has_properties(args=contains_exactly("mock_id", "new_value"))
            ),
        )
        assert_that(
            attribute_mock.update_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        item_mapper.update_request.return_value, "mock_id", "new_value"
                    )
                )
            ),
        )

        assert_that(
            update_requests,
            contains_exactly(
                item_mapper.update_request.return_value, attribute_request
            ),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_update_request_simple_list_model(self, connection):
        """Tests the validity of built update requests for a list model."""
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.update_request.return_value = base_request

        attribute_requests = [MagicMock(connection=connection) for _ in range(3)]
        attribute_mocks = [
            MagicMock(
                spec=DatabaseAttribute,
                request=attribute_requests[i],
                connection=connection,
            )
            for i in range(3)
        ]
        for i in range(3):
            attribute_mocks[i].update_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(item_mapper, attribute_mocks)
        # Connection used for the base request
        database_item.connection = connection

        update_requests = database_item.update_request(
            "mock_id", ["up_login", "up_name", "up_contact"]
        )

        # As a side effect, the connection must have been set up on all requests
        # returned in search_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.update_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        "mock_id",
                        contains_exactly(
                            "up_login",
                            "up_name",
                            "up_contact",
                        ),
                    )
                )
            ),
        )
        for attribute, value in zip(
            attribute_mocks, ["up_login", "up_name", "up_contact"]
        ):
            assert_that(
                attribute.update_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.update_request.return_value, "mock_id", value
                        )
                    )
                ),
            )

        assert_that(
            update_requests,
            contains_exactly(
                item_mapper.update_request.return_value,
                contains_exactly(*attribute_requests),
            ),
        )

    @patch("backo.database.connection.DatabaseConnection", autospec=True)
    def test_update_request_simple_dict_model(self, connection):
        """Tests the validity of built update requests for a dict model."""
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.update_request.return_value = base_request

        attribute_requests = [MagicMock(connection=connection) for _ in range(3)]
        attribute_mocks = [
            MagicMock(
                spec=DatabaseAttribute,
                request=attribute_requests[i],
                connection=connection,
            )
            for i in range(3)
        ]
        for i in range(3):
            attribute_mocks[i].update_request.return_value = attribute_requests[i]

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

        update_requests = database_item.update_request(
            "mock_id", {"login": "up_login", "name": "up_name", "contact": "up_contact"}
        )

        # As a side effect, the connection must have been set up on all requests
        # returned in search_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.update_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        "mock_id",
                        has_entries(
                            {
                                "login": "up_login",
                                "name": "up_name",
                                "contact": "up_contact",
                            }
                        ),
                    )
                )
            ),
        )
        for attribute, value in zip(
            attribute_mocks, ["up_login", "up_name", "up_contact"]
        ):
            assert_that(
                attribute.update_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.update_request.return_value, "mock_id", value
                        )
                    )
                ),
            )

        assert_that(
            update_requests,
            contains_exactly(
                item_mapper.update_request.return_value,
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
    def test_update_request_with_complex_nested_attributes(self, connection):
        """Tests the validity of built update requests for a model with
        attributes nested in dicts and lists.
        """
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.update_request.return_value = base_request

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
            attribute_mocks[i].update_request.return_value = attribute_requests[i]

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

        update_requests = database_item.update_request(
            "mock_id",
            {
                "name": "up_name",
                "nested": {
                    "data": [
                        [12, 13],
                        "data_2",
                        {"nested_data": "up_nested_value"},
                    ],
                    "time": "up_time",
                },
            },
        )

        # As a side effect, the connection must have been set up on all requests
        # returned in search_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.update_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        "mock_id",
                        has_entries(
                            {
                                "name": "up_name",
                                "nested": has_entries(
                                    {
                                        "data": contains_exactly(
                                            contains_exactly(12, 13),
                                            "data_2",
                                            has_entries(
                                                {"nested_data": "up_nested_value"}
                                            ),
                                        ),
                                        "time": "up_time",
                                    }
                                ),
                            }
                        ),
                    )
                )
            ),
        )
        for attribute, value in zip(
            attribute_mocks,
            [
                "up_name",
                12,
                13,
                "data_2",
                "up_nested_value",
                "up_time",
            ],
        ):
            assert_that(
                attribute.update_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.update_request.return_value, "mock_id", value
                        )
                    )
                ),
            )

        assert_that(
            update_requests,
            contains_exactly(
                item_mapper.update_request.return_value,
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
    def test_update_multiple_request_attribute(self, connection):
        """Tests the validity of built update requests for a model with
        attributes that require multiple requests nested in dicts and lists.
        """
        base_request = MagicMock(connection=None)
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.update_request.return_value = base_request

        attribute_requests = [MagicMock() for _ in range(5)]
        attribute_mocks = [
            MagicMock(
                spec=DatabaseAttribute,
                request=attribute_requests[i],
                connection=connection,
            )
            for i in range(2)
        ]
        attribute_mocks[0].update_request.return_value = {
            "request1": attribute_requests[0],
            "request2": attribute_requests[1],
        }
        attribute_mocks[1].update_request.return_value = [
            attribute_requests[2],
            {"req1": attribute_requests[3], "req2": attribute_requests[4]},
        ]

        database_item = DatabaseItem(
            item_mapper,
            {"foo": attribute_mocks[0], "nested": {"bar": attribute_mocks[1]}},
        )
        # Connection used for the base request
        database_item.connection = connection

        update_requests = database_item.update_request(
            "mock_id",
            {"foo": "foo_value", "nested": {"bar": ["bar_value_1", "bar_value_2"]}},
        )

        # As a side effect, the connection must have been set up on all requests
        # returned in search_requests
        assert_that(base_request, has_properties(connection=connection))
        for request in attribute_requests:
            assert_that(request, has_properties(connection=connection))

        assert_that(
            item_mapper.update_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        "mock_id",
                        has_entries(
                            {
                                "foo": "foo_value",
                                "nested": has_entries(
                                    {"bar": ["bar_value_1", "bar_value_2"]}
                                ),
                            }
                        ),
                    )
                )
            ),
        )
        for attribute, value in zip(
            attribute_mocks,
            ["foo_value", contains_exactly("bar_value_1", "bar_value_2")],
        ):
            assert_that(
                attribute.update_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.update_request.return_value, "mock_id", value
                        )
                    )
                ),
            )

        assert_that(
            update_requests,
            contains_exactly(
                item_mapper.update_request.return_value,
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
