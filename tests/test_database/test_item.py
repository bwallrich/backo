import unittest
from unittest.mock import MagicMock, patch

from hamcrest import (
    assert_that,
    contains_exactly,
    has_entries,
    contains_inanyorder,
    has_properties,
)

from backo.database.item import DatabaseItem, DatabaseAttribute, ItemMapper
from backo.database.request import (
    DatabaseSearchRequest,
    DatabaseCreateRequest,
    DatabaseDeleteRequest,
    DatabaseUpdateRequest,
)


class TestDatabaseItem(unittest.TestCase):
    def test_init_database_item(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_mocks = [MagicMock(spec=DatabaseAttribute) for i in range(6)]

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
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_mocks = [MagicMock(spec=DatabaseAttribute) for i in range(6)]

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

    def test_search_request_simple_item(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseSearchRequest) for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
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

        search_requests = database_item.search_request("mock_id")

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

    def test_search_request_with_complex_nested_attributes(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseSearchRequest) for _ in range(6)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
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

        search_requests = database_item.search_request("mock_id")

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

    def test_search_multiple_request_attribute(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseSearchRequest) for _ in range(5)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
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

        search_requests = database_item.search_request("mock_id")

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

    def test_create_request_simple_item(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseCreateRequest) for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
            for i in range(3)
        ]
        for i in range(3):
            attribute_mocks[i].create_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(
            item_mapper,
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
            item_mapper.create_request.call_args_list,
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
                            item_mapper.create_request.return_value, value
                        )
                    )
                ),
            )

        assert_that(
            create_requests,
            contains_exactly(
                item_mapper.create_request.return_value,
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
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseSearchRequest) for _ in range(6)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
            for i in range(6)
        ]
        for i in range(6):
            attribute_mocks[i].create_request.return_value = attribute_requests[i]

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
            item_mapper.create_request.call_args_list,
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
                            item_mapper.create_request.return_value, value
                        )
                    )
                ),
            )

        assert_that(
            create_requests,
            contains_exactly(
                item_mapper.create_request.return_value,
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

    def test_create_multiple_request_attribute(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseCreateRequest) for _ in range(5)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
            for i in range(2)
        ]
        attribute_mocks[0].create_request.return_value = {
            "request1": attribute_requests[0],
            "request2": attribute_requests[1],
        }
        attribute_mocks[1].create_request.return_value = [
            attribute_requests[2],
            {"req1": attribute_requests[3], "req2": attribute_requests[4]},
        ]

        database_item = DatabaseItem(
            item_mapper,
            {"foo": attribute_mocks[0], "nested": {"bar": attribute_mocks[1]}},
        )

        create_requests = database_item.create_request(
            {"foo": "foo_value", "nested": {"bar": ["bar_value_1", "bar_value_2"]}}
        )

        assert_that(
            item_mapper.create_request.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        has_entries(
                            {
                                "foo": "foo_value",
                                "nested": has_entries(
                                    {"bar": ["bar_value_1", "bar_value_2"]}
                                ),
                            }
                        )
                    )
                )
            ),
        )
        for attribute, value in zip(
            attribute_mocks,
            ["foo_value", contains_exactly("bar_value_1", "bar_value_2")],
        ):
            assert_that(
                attribute.create_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.create_request.return_value, value
                        )
                    )
                ),
            )

        assert_that(
            create_requests,
            contains_exactly(
                item_mapper.create_request.return_value,
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

    def test_delete_request_simple_item(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseDeleteRequest) for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
            for i in range(3)
        ]
        for i in range(3):
            attribute_mocks[i].delete_request.return_value = attribute_requests[i]

        database_item = DatabaseItem(
            item_mapper,
            {
                "login": attribute_mocks[0],
                "name": attribute_mocks[1],
                "contact": attribute_mocks[2],
            },
        )

        delete_requests = database_item.delete_request("mock_id")

        assert_that(
            item_mapper.delete_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )
        for attribute in attribute_mocks:
            assert_that(
                attribute.delete_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.delete_request.return_value, "mock_id"
                        )
                    )
                ),
            )

        assert_that(
            delete_requests,
            contains_exactly(
                item_mapper.delete_request.return_value,
                has_entries(
                    {
                        "login": attribute_requests[0],
                        "name": attribute_requests[1],
                        "contact": attribute_requests[2],
                    }
                ),
            ),
        )

    def test_delete_request_with_complex_nested_attributes(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseSearchRequest) for _ in range(6)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
            for i in range(6)
        ]
        for i in range(6):
            attribute_mocks[i].delete_request.return_value = attribute_requests[i]

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

        delete_requests = database_item.delete_request("mock_id")

        assert_that(
            item_mapper.delete_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )
        for attribute in attribute_mocks:
            assert_that(
                attribute.delete_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.delete_request.return_value, "mock_id"
                        )
                    )
                ),
            )

        assert_that(
            delete_requests,
            contains_exactly(
                item_mapper.delete_request.return_value,
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

    def test_delete_multiple_request_attribute(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseDeleteRequest) for _ in range(5)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
            for i in range(2)
        ]
        attribute_mocks[0].delete_request.return_value = {
            "request1": attribute_requests[0],
            "request2": attribute_requests[1],
        }
        attribute_mocks[1].delete_request.return_value = [
            attribute_requests[2],
            {"req1": attribute_requests[3], "req2": attribute_requests[4]},
        ]

        database_item = DatabaseItem(
            item_mapper,
            {"foo": attribute_mocks[0], "nested": {"bar": attribute_mocks[1]}},
        )

        delete_requests = database_item.delete_request("mock_id")

        assert_that(
            item_mapper.delete_request.call_args_list,
            contains_exactly(has_properties(args=contains_exactly("mock_id"))),
        )
        for attribute in attribute_mocks:
            assert_that(
                attribute.delete_request.call_args_list,
                contains_exactly(
                    has_properties(
                        args=contains_exactly(
                            item_mapper.delete_request.return_value, "mock_id"
                        )
                    )
                ),
            )

        assert_that(
            delete_requests,
            contains_exactly(
                item_mapper.delete_request.return_value,
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

    def test_update_request_simple_item(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseUpdateRequest) for _ in range(3)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
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

        update_requests = database_item.update_request(
            "mock_id", {"login": "up_login", "name": "up_name", "contact": "up_contact"}
        )

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

    def test_update_request_with_complex_nested_attributes(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseUpdateRequest) for _ in range(6)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
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

    def test_update_multiple_request_attribute(self):
        item_mapper = MagicMock(spec=ItemMapper)

        attribute_requests = [MagicMock(spec=DatabaseUpdateRequest) for _ in range(5)]
        attribute_mocks = [
            MagicMock(spec=DatabaseAttribute, request=attribute_requests[i])
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

        update_requests = database_item.update_request(
            "mock_id",
            {"foo": "foo_value", "nested": {"bar": ["bar_value_1", "bar_value_2"]}},
        )

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

    def test_load_simple_item(self):
        """Tests DatabaseItem.load method for a simple item, without references.

        The item must be loaded from the mocked LDAP response.
        """

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
        """Tests DatabaseItem.load method for a simple item, without references.

        The item must be loaded from the mocked LDAP response.
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

    def test_load_item_multiple_request_attribute(self):
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
