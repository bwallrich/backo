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
    equal_to,
)

from backo.database.engine import DatabaseEngine
from backo.database.connection import DatabaseConnection
from backo.error import NotFoundError


@patch("backo.database.item.DatabaseItem", autospec=True)
@patch("backo.database.connection.DatabaseConnection", autospec=True)
class TestDatabaseEngine(unittest.TestCase):
    """
    Test LdapConnector features
    """

    def test_init_engine(self, connection, database_item):
        """Tests DatabaseEngine initialization. Ensures the database_item is
        properly initialized by the DatabaseEngine.
        """

        engine = DatabaseEngine(connection.return_value, database_item.return_value)

        assert_that(
            database_item.return_value.set_default_connection.call_args_list,
            contains_exactly(
                has_properties(args=contains_exactly(connection.return_value))
            ),
        )

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
            MagicMock(response=mock_responses[i], connection=connection.return_value)
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

        for mock_request in mock_queries[4:]:
            mock_connection = MagicMock(spec=DatabaseConnection)
            mock_connection.execute_search.side_effect = mock_execute_search
            mock_request.connection = mock_connection

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
                    for mock_request in mock_queries[:4]
                ]
            ),
        )
        for mock_request in mock_queries[4:]:
            assert_that(
                mock_request.connection.execute_search.call_args_list,
                contains_exactly(has_properties(args=contains_exactly(mock_request))),
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

        Must raise a NotFoundError.
        """

        engine = DatabaseEngine(connection.return_value, database_item.return_value)

        database_item.return_value.search_request.return_value = (
            MagicMock(connection=connection.return_value),
            {},
        )
        connection.return_value.execute_search.side_effect = NotFoundError(
            "item not found"
        )

        # Real call to the method under test
        assert_that(calling(engine.search).with_args("mock_id"), raises(NotFoundError))

    def test_create(self, connection, database_item):
        """Tests LdapSearchEngine.create method."""

        engine = DatabaseEngine(connection.return_value, database_item.return_value)

        database_item.return_value.created_id.return_value = "unique_id_of_the_new_item"

        mock_responses = [MagicMock() for _ in range(9)]  # Database specific type
        mock_queries = [
            MagicMock(response=mock_responses[i], connection=connection.return_value)
            for i in range(9)
        ]

        database_item.return_value.create_request.return_value = (
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

        def mock_execute_create(create_request):
            return create_request.response

        connection.return_value.execute_create.side_effect = mock_execute_create

        connection.return_value.execute_search.side_effect = mock_execute_create

        for mock_request in mock_queries[4:]:
            mock_connection = MagicMock(spec=DatabaseConnection)
            mock_connection.execute_create.side_effect = mock_execute_create
            mock_request.connection = mock_connection

        item_to_create = {"name": "new_item", "field": "some_value", "port": 1312}
        # Real call to the method under test
        item_id = engine.create(item_to_create)

        assert_that(
            database_item.return_value.create_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        # The call argument is checked using has_entries because it
                        # would be OK to pass a copy of the item_to_create as argument
                        has_entries(item_to_create)
                    )
                )
            ),
        )

        # Ensure create was called with appropriate parameters.
        assert_that(
            connection.return_value.execute_create.call_args_list,
            contains_inanyorder(
                *[
                    has_properties(args=contains_exactly(mock_request))
                    for mock_request in mock_queries[:4]
                ]
            ),
        )
        for mock_request in mock_queries[4:]:
            assert_that(
                mock_request.connection.execute_create.call_args_list,
                contains_exactly(has_properties(args=contains_exactly(mock_request))),
            )

        assert_that(
            database_item.return_value.created_id.call_args_list,
            contains_exactly(has_properties(args=contains_exactly(mock_responses[0]))),
        )

        assert_that(item_id, equal_to("unique_id_of_the_new_item"))

    def test_delete(self, connection, database_item):
        """Tests LdapSearchEngine.delete method for an existing item."""

        engine = DatabaseEngine(connection.return_value, database_item.return_value)

        mock_responses = [MagicMock() for _ in range(9)]  # Database specific type
        mock_queries = [
            MagicMock(response=mock_responses[i], connection=connection.return_value)
            for i in range(9)
        ]

        database_item.return_value.delete_request.return_value = (
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

        def mock_execute_delete(delete_request):
            return delete_request.response

        connection.return_value.execute_delete.side_effect = mock_execute_delete

        for mock_request in mock_queries[4:]:
            mock_connection = MagicMock(spec=DatabaseConnection)
            mock_connection.execute_delete.side_effect = mock_execute_delete
            mock_request.connection = mock_connection

        # Real call to the method under test
        engine.delete("mock_id")

        assert_that(
            database_item.return_value.delete_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )

        # Ensure search was called with appropriate parameters.
        assert_that(
            connection.return_value.execute_delete.call_args_list,
            contains_inanyorder(
                *[
                    has_properties(args=contains_exactly(mock_request))
                    for mock_request in mock_queries[:4]
                ]
            ),
        )
        for mock_request in mock_queries[4:]:
            assert_that(
                mock_request.connection.execute_delete.call_args_list,
                contains_exactly(has_properties(args=contains_exactly(mock_request))),
            )

    def test_save(self, connection, database_item):
        """Tests LdapSearchEngine.save method for an existing item."""

        engine = DatabaseEngine(connection.return_value, database_item.return_value)

        mock_responses = [MagicMock() for _ in range(9)]  # Database specific type
        mock_queries = [
            MagicMock(response=mock_responses[i], connection=connection.return_value)
            for i in range(9)
        ]

        database_item.return_value.update_request.return_value = (
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

        def mock_execute_update(update_request):
            return update_request.response

        connection.return_value.execute_update.side_effect = mock_execute_update

        for mock_request in mock_queries[4:]:
            mock_connection = MagicMock(spec=DatabaseConnection)
            mock_connection.execute_update.side_effect = mock_execute_update
            mock_request.connection = mock_connection

        updated_item = {
            "name": "updated_item",
            "field": "up_to_date_value",
            "port": 1213,
        }

        # Real call to the method under test
        engine.save("mock_id", updated_item)

        assert_that(
            database_item.return_value.update_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly("mock_id", has_entries(updated_item))
                )
            ),
        )

        # Ensure search was called with appropriate parameters.
        assert_that(
            connection.return_value.execute_update.call_args_list,
            contains_inanyorder(
                *[
                    has_properties(args=contains_exactly(mock_request))
                    for mock_request in mock_queries[:4]
                ]
            ),
        )
        for mock_request in mock_queries[4:]:
            assert_that(
                mock_request.connection.execute_update.call_args_list,
                contains_exactly(has_properties(args=contains_exactly(mock_request))),
            )
