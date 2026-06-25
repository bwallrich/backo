"""DatabaseItem load tests"""

import unittest
from unittest.mock import MagicMock

from hamcrest import (
    assert_that,
    contains_exactly,
    has_entries,
    has_properties,
    equal_to,
)

from backo.database.item import DatabaseItem
from backo.database.attribute import DatabaseAttribute
from backo.database.mapper import ItemMapper


class TestDatabaseItemLoad(unittest.TestCase):
    """Tests item loading depending on the complexity of the model."""

    def test_load_single_attribute_model(self):
        """Tests database item loading for a single attribute model."""

        root_response = MagicMock()
        mock_item_mapper = MagicMock(spec=ItemMapper)
        mock_item_mapper.load.return_value = None

        attribute_response = MagicMock()
        attribute_mock = MagicMock(spec=DatabaseAttribute, response=attribute_response)
        database_item = DatabaseItem(mock_item_mapper, attribute_mock)

        attribute_mock.load.return_value = "John Doe"

        # Real call to the method under test
        item = database_item.load(root_response, attribute_response)

        assert_that(
            mock_item_mapper.load.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(root_response))),
        )

        assert_that(
            attribute_mock.load.call_args_list,
            contains_exactly(
                has_properties(args=contains_exactly(root_response, attribute_response))
            ),
        )

        assert_that(
            item,
            equal_to("John Doe"),
        )

    def test_load_simple_list_model(self):
        """Tests database item loading for a list model."""

        root_response = MagicMock()
        mock_item_mapper = MagicMock(spec=ItemMapper)
        mock_item_mapper.load.return_value = []

        attribute_responses = [MagicMock() for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, response=attribute_responses[i])
            for i in range(3)
        ]
        database_item = DatabaseItem(mock_item_mapper, attribute_mocks)

        attribute_mocks[0].load.return_value = "jdoe"
        attribute_mocks[1].load.return_value = "John Doe"
        attribute_mocks[2].load.return_value = ["mail1@example.org", "mail2@jdoe.fr"]

        # Real call to the method under test
        item = database_item.load(root_response, attribute_responses)

        assert_that(
            mock_item_mapper.load.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(root_response))),
        )

        for attribute, response in zip(attribute_mocks, attribute_responses):
            assert_that(
                attribute.load.call_args_list,
                contains_exactly(
                    has_properties(args=contains_exactly(root_response, response))
                ),
            )

        assert_that(
            item,
            contains_exactly(
                "jdoe",
                "John Doe",
                contains_exactly("mail1@example.org", "mail2@jdoe.fr"),
            ),
        )

    def test_load_simple_dict_model(self):
        """Tests database item loading for a dict model."""

        root_response = MagicMock()
        mock_item_mapper = MagicMock(spec=ItemMapper)
        mock_item_mapper.load.return_value = {}

        attribute_responses = [MagicMock() for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, response=attribute_responses[i])
            for i in range(3)
        ]
        database_item = DatabaseItem(
            mock_item_mapper,
            {
                "login": attribute_mocks[0],
                "name": attribute_mocks[1],
                "contact": attribute_mocks[2],
            },
        )

        attribute_mocks[0].load.return_value = "jdoe"
        attribute_mocks[1].load.return_value = "John Doe"
        attribute_mocks[2].load.return_value = ["mail1@example.org", "mail2@jdoe.fr"]

        # Real call to the method under test
        item = database_item.load(
            root_response,
            {
                "login": attribute_responses[0],
                "name": attribute_responses[1],
                "contact": attribute_responses[2],
            },
        )

        assert_that(
            mock_item_mapper.load.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(root_response))),
        )

        for attribute, response in zip(attribute_mocks, attribute_responses):
            assert_that(
                attribute.load.call_args_list,
                contains_exactly(
                    has_properties(args=contains_exactly(root_response, response))
                ),
            )

        assert_that(
            item,
            has_entries(
                {
                    "login": "jdoe",
                    "name": "John Doe",
                    "contact": contains_exactly("mail1@example.org", "mail2@jdoe.fr"),
                }
            ),
        )

    def test_load_item_with_complex_nested_attributes(self):
        """Tests database item loading for a model with attributes nested in
        dicts and lists.
        """

        root_response = MagicMock()
        mock_item_mapper = MagicMock(spec=ItemMapper)
        mock_item_mapper.load.return_value = {}

        attribute_responses = [MagicMock() for _ in range(6)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, response=attribute_responses[i])
            for i in range(6)
        ]
        database_item = DatabaseItem(
            mock_item_mapper,
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

        attribute_mocks[0].load.return_value = "jdoe"
        attribute_mocks[1].load.return_value = 13
        attribute_mocks[2].load.return_value = 12
        attribute_mocks[3].load.return_value = "some_value"
        attribute_mocks[4].load.return_value = "nested_data_value"
        attribute_mocks[5].load.return_value = "now"

        # Real call to the method under test
        item = database_item.load(
            root_response,
            {
                "name": attribute_responses[0],
                "nested": {
                    "data": [
                        [attribute_responses[1], attribute_responses[2]],
                        attribute_responses[3],
                        {"nested_data": attribute_responses[4]},
                    ],
                    "time": attribute_responses[5],
                },
            },
        )

        assert_that(
            mock_item_mapper.load.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(root_response))),
        )

        for attribute, response in zip(attribute_mocks, attribute_responses):
            assert_that(
                attribute.load.call_args_list,
                contains_exactly(
                    has_properties(args=contains_exactly(root_response, response))
                ),
            )

        assert_that(
            item,
            has_entries(
                {
                    "name": "jdoe",
                    "nested": has_entries(
                        {
                            "data": contains_exactly(
                                contains_exactly(13, 12),
                                "some_value",
                                has_entries({"nested_data": "nested_data_value"}),
                            ),
                            "time": "now",
                        }
                    ),
                }
            ),
        )

    def test_load_item_multiple_request_attribute(self):
        """Tests database item loading for  a model with
        attributes that require multiple requests nested in dicts and lists.
        """

        base_response = MagicMock()
        item_mapper = MagicMock(spec=ItemMapper)
        item_mapper.load.return_value = {}

        attribute_responses = [MagicMock() for _ in range(5)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_responses[i])
            for i in range(2)
        ]

        database_item = DatabaseItem(
            item_mapper,
            {"foo": attribute_mocks[0], "nested": {"bar": attribute_mocks[1]}},
        )
        attribute_mocks[0].load.return_value = "foo_value"
        attribute_mocks[1].load.return_value = ["bar_value_1", "bar_value_2"]

        item = database_item.load(
            base_response,
            {
                "foo": {
                    "request1": attribute_responses[0],
                    "request2": attribute_responses[1],
                },
                "nested": {
                    "bar": [
                        attribute_responses[2],
                        {
                            "req1": attribute_responses[3],
                            "req2": attribute_responses[4],
                        },
                    ]
                },
            },
        )

        assert_that(
            item_mapper.load.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(base_response))),
        )

        for attribute, response in zip(
            attribute_mocks,
            [
                has_entries(
                    {
                        "request1": attribute_responses[0],
                        "request2": attribute_responses[1],
                    }
                ),
                contains_exactly(
                    attribute_responses[2],
                    has_entries(
                        {"req1": attribute_responses[3], "req2": attribute_responses[4]}
                    ),
                ),
            ],
        ):
            assert_that(
                attribute.load.call_args_list,
                contains_exactly(
                    has_properties(args=contains_exactly(base_response, response))
                ),
            )

        assert_that(
            item,
            has_entries(
                {
                    "foo": "foo_value",
                    "nested": has_entries(
                        {"bar": contains_exactly("bar_value_1", "bar_value_2")}
                    ),
                },
            ),
        )
