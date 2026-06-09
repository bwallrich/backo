"""
Test module for backo.database.engine.py
"""

import unittest

from unittest.mock import patch, MagicMock

from hamcrest import (
    assert_that,
    contains_exactly,
    has_properties,
    has_entries,
    contains_inanyorder,
    calling,
    raises,
)

from backo.database.engine import DatabaseEngine
from backo.error import NotFoundError
from backo.database.request import DatabaseSearchRequest


@patch("backo.database.item.DatabaseItem", autospec=True)
@patch("backo.database.connection.DatabaseConnection", autospec=True)
class TestDatabaseEngine(unittest.TestCase):
    """
    Test LdapConnector features
    """

    def test_search(self, connection, database_item):
        """Tests LdapSearchEngine.search method for an existing item.

        The returned item must correspond to the item loaded by the database_item
        from the connection.search results.
        """

        engine = DatabaseEngine(connection.return_value, database_item.return_value)

        database_item.return_value.load.return_value = {
            "mock": "attribute",
            "nested": {"item": "nested_attribute"},
            "list": "aggregate_attribute",
            "nested_list": [
                ["item1", "item2"],
                "some_value",
                {"nested_in_list": "object"},
            ],
        }

        mock_responses = [MagicMock() for _ in range(9)]  # Database specific type
        mock_queries = [
            MagicMock(spec=DatabaseSearchRequest, response=mock_responses[i])
            for i in range(9)
        ]

        database_item.return_value.search_request.return_value = (
            mock_queries[0],
            {
                "mock": mock_queries[1],
                "nested": {"item": mock_queries[2]},
                "list": [mock_queries[3], mock_queries[4]],
                "nested_list": [
                    [mock_queries[5], mock_queries[6]],
                    mock_queries[7],
                    {"nested_in_list": mock_queries[8]},
                ],
            },
        )

        def mock_execute_search(search_request):
            return search_request.response

        connection.return_value.execute_search.side_effect = mock_execute_search

        # Real call to the method under test
        item = engine.search("mock_id")

        assert_that(
            database_item.return_value.search_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )

        # Ensure search was called with appropriate parameters.
        assert_that(
            connection.return_value.execute_search.call_args_list,
            contains_inanyorder(
                *[
                    has_properties(args=contains_exactly(mock_request))
                    for mock_request in mock_queries
                ]
            ),
        )

        assert_that(
            database_item.return_value.load.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        mock_responses[0],
                        has_entries(
                            {
                                "mock": mock_responses[1],
                                "nested": has_entries({"item": mock_responses[2]}),
                                "list": contains_exactly(
                                    mock_responses[3], mock_responses[4]
                                ),
                                "nested_list": contains_exactly(
                                    contains_exactly(
                                        mock_responses[5], mock_responses[6]
                                    ),
                                    mock_responses[7],
                                    has_entries({"nested_in_list": mock_responses[8]}),
                                ),
                            }
                        ),
                    )
                )
            ),
        )

        assert_that(
            item,
            has_entries(
                {
                    "_id": "mock_id",
                    "mock": "attribute",
                    "nested": has_entries({"item": "nested_attribute"}),
                    "list": "aggregate_attribute",
                    "nested_list": contains_exactly(
                        contains_exactly("item1", "item2"),
                        "some_value",
                        has_entries({"nested_in_list": "object"}),
                    ),
                }
            ),
        )

    def test_search_not_found(self, connection, database_item):
        """Tests LdapSearchEngine.search method for an non existing item.

        Must return a NotFoundError.
        """

        engine = DatabaseEngine(connection.return_value, database_item.return_value)

        database_item.return_value.search_request.return_value = (
            MagicMock(spec=DatabaseSearchRequest),
            {},
        )
        connection.return_value.execute_search.side_effect = NotFoundError(
            "item not found"
        )

        # Real call to the method under test
        assert_that(calling(engine.search).with_args("mock_id"), raises(NotFoundError))
