import unittest
from unittest.mock import MagicMock

from hamcrest import (
    assert_that,
    contains_exactly,
    has_entries,
    contains_inanyorder,
    has_properties,
)

from backo.database.item import DatabaseItem, IdMapper
from backo.database.request import DatabaseSearchRequest, DatabaseCreateRequest


class TestDatabaseItem(unittest.TestCase):
    def test_search_request_simple_item(self):
        id_mapper = MagicMock(spec=IdMapper)

        attribute_requests = [MagicMock(spec=DatabaseSearchRequest) for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseItem, request=attribute_requests[i])
            for i in range(3)
        ]
        for i in range(3):
            attribute_mocks[i].search_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(
            id_mapper,
            {
                "login": attribute_mocks[0],
                "name": attribute_mocks[1],
                "contact": attribute_mocks[2],
            },
        )

        search_requests = database_item.search_request("mock_id")

        assert_that(
            id_mapper.search_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )
        for attribute in attribute_mocks:
            assert_that(
                attribute.search_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(id_mapper.search_request.return_value)
                    )
                ),
            )

        assert_that(
            search_requests,
            contains_exactly(
                id_mapper.search_request.return_value,
                has_entries(
                    {
                        "login": attribute_requests[0],
                        "name": attribute_requests[1],
                        "contact": attribute_requests[2],
                    }
                ),
            ),
        )

    def test_search_request_with_complex_nested_attributes(self):
        id_mapper = MagicMock(spec=IdMapper)

        attribute_requests = [MagicMock(spec=DatabaseSearchRequest) for _ in range(6)]
        attribute_mocks = [
            MagicMock(spec=DatabaseItem, request=attribute_requests[i])
            for i in range(6)
        ]
        for i in range(6):
            attribute_mocks[i].search_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(
            id_mapper,
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

        search_requests = database_item.search_request("mock_id")

        assert_that(
            id_mapper.search_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )
        for attribute in attribute_mocks:
            assert_that(
                attribute.search_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(id_mapper.search_request.return_value)
                    )
                ),
            )

        assert_that(
            search_requests,
            contains_exactly(
                id_mapper.search_request.return_value,
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

    def test_create_request_simple_item(self):
        id_mapper = MagicMock(spec=IdMapper)

        attribute_requests = [MagicMock(spec=DatabaseCreateRequest) for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseItem, request=attribute_requests[i])
            for i in range(3)
        ]
        for i in range(3):
            attribute_mocks[i].create_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(
            id_mapper,
            {
                "login": attribute_mocks[0],
                "name": attribute_mocks[1],
                "contact": attribute_mocks[2],
            },
        )

        create_requests = database_item.create_request(
            {"login": "new_login", "name": "new_name", "contact": "new_contact"}
        )

        assert_that(
            id_mapper.create_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        has_entries(
                            {
                                "login": "new_login",
                                "name": "new_name",
                                "contact": "new_contact",
                            }
                        )
                    )
                )
            ),
        )
        for attribute, value in zip(
            attribute_mocks, ["new_login", "new_name", "new_contact"]
        ):
            assert_that(
                attribute.create_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            id_mapper.create_request.return_value, value
                        )
                    )
                ),
            )

        assert_that(
            create_requests,
            contains_exactly(
                id_mapper.create_request.return_value,
                has_entries(
                    {
                        "login": attribute_requests[0],
                        "name": attribute_requests[1],
                        "contact": attribute_requests[2],
                    }
                ),
            ),
        )

    def test_create_request_with_complex_nested_attributes(self):
        id_mapper = MagicMock(spec=IdMapper)

        attribute_requests = [MagicMock(spec=DatabaseSearchRequest) for _ in range(6)]
        attribute_mocks = [
            MagicMock(spec=DatabaseItem, request=attribute_requests[i])
            for i in range(6)
        ]
        for i in range(6):
            attribute_mocks[i].create_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(
            id_mapper,
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

        create_requests = database_item.create_request(
            {
                "name": "new_name",
                "nested": {
                    "data": [
                        [13, 12],
                        "data_1",
                        {"nested_data": "new_nested_value"},
                    ],
                    "time": "new_time",
                },
            }
        )

        assert_that(
            id_mapper.create_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        has_entries(
                            {
                                "name": "new_name",
                                "nested": has_entries(
                                    {
                                        "data": contains_exactly(
                                            contains_exactly(13, 12),
                                            "data_1",
                                            has_entries(
                                                {"nested_data": "new_nested_value"}
                                            ),
                                        ),
                                        "time": "new_time",
                                    }
                                ),
                            }
                        )
                    )
                )
            ),
        )
        for attribute, value in zip(
            attribute_mocks,
            [
                "new_name",
                13,
                12,
                "data_1",
                "new_nested_value",
                "new_time",
            ],
        ):
            assert_that(
                attribute.create_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            id_mapper.create_request.return_value, value
                        )
                    )
                ),
            )

        assert_that(
            create_requests,
            contains_exactly(
                id_mapper.create_request.return_value,
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

    def test_load_simple_item(self):
        """Tests LdapItem.load method for a simple item, without references.

        The item must be loaded from the mocked LDAP response.
        """

        root_response = MagicMock()
        attribute_responses = [MagicMock() for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseItem, response=attribute_responses[i])
            for i in range(3)
        ]
        database_item = DatabaseItem(
            MagicMock(spec=IdMapper),
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

        for i in range(len(attribute_mocks)):
            assert_that(
                attribute_mocks[i].load.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(root_response, attribute_responses[i])
                    )
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
        """Tests LdapItem.load method for a simple item, without references.

        The item must be loaded from the mocked LDAP response.
        """

        root_response = MagicMock()
        attribute_responses = [MagicMock() for _ in range(6)]
        attribute_mocks = [
            MagicMock(spec=DatabaseItem, response=attribute_responses[i])
            for i in range(6)
        ]
        database_item = DatabaseItem(
            MagicMock(spec=IdMapper),
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

        for i in range(len(attribute_mocks)):
            assert_that(
                attribute_mocks[i].load.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(root_response, attribute_responses[i])
                    )
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
