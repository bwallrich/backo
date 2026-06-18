"""Tests nested data path utilities"""

import unittest

from hamcrest import (
    assert_that,
    equal_to,
    calling,
    raises,
    has_entries,
    contains_exactly,
)

from backo.utils.nested_data_path import find, update, delete, PathError


class TestNestedDataPathFind(unittest.TestCase):
    """Tests for the find method"""

    def test_find(self):
        """Tests a trivial find, without nested structures."""
        assert_that(
            find(
                {"data": "found!"},
                ["data"],
            ),
            equal_to("found!"),
        )

    def test_find_value(self):
        """Tests a path to a value that is not a dict or a list in a nested
        structure returns the value."""

        assert_that(
            find(
                {"data": {"nested": [0, {"dict": {"value": [-1, 0, "found!"]}}]}},
                ["data", "nested", 1, "dict", "value", 2],
            ),
            equal_to("found!"),
        )

    def test_find_dict(self):
        """Tests a path to a dict in a nested structure returns the dict."""
        assert_that(
            find(
                {"data": {"nested": [0, {"dict": {"value": [-1, 0, "found!"]}}]}},
                ["data", "nested", 1, "dict"],
            ),
            has_entries({"value": contains_exactly(-1, 0, "found!")}),
        )

    def test_find_list(self):
        """Tests a path to a list in a nested structure returns the list."""
        assert_that(
            find(
                {"data": {"nested": [0, {"dict": {"value": [-1, 0, "found!"]}}]}},
                ["data", "nested", 1, "dict", "value"],
            ),
            contains_exactly(-1, 0, "found!"),
        )

    def test_find_bad_list_path_on_scalar(self):
        """Tests if a PathError is raised if a list index reaches a leaf."""
        data = {"data": "bip"}
        path = ["data", 2]
        assert_that(calling(find).with_args(data, path), raises(PathError))

    def test_find_bad_dict_path_on_scalar(self):
        """Tests if a PathError is raised if a key reaches a leaf."""
        data = {"data": "bip"}
        path = ["data", "key"]
        assert_that(calling(find).with_args(data, path), raises(PathError))

    def test_find_bad_dict_path_in_root_list(self):
        """Tests if a PathError is raised if a key reaches the root list."""
        data = ["data", []]
        path = ["key"]
        assert_that(calling(find).with_args(data, path), raises(PathError))

    def test_find_bad_dict_path_in_nested_list(self):
        """Tests if a PathError is raised if a key reaches a nested list."""
        data = {"data": []}
        path = ["data", "key"]
        assert_that(calling(find).with_args(data, path), raises(PathError))


class TestNestedDataPathUpdate(unittest.TestCase):
    """Tests for the update method"""

    def test_update_existing_value_in_list(self):
        """Tests if an existing value in a nested list is updated."""
        data = {"data": {"nested": [0, {"dict": {"value": [-1, 0, "found!"]}}]}}
        path = ["data", "nested", 1, "dict", "value", 2]
        update(data, path, "Updated!")
        assert_that(find(data, path), equal_to("Updated!"))

    def test_update_existing_value_in_dict(self):
        """Tests if an existing value in a nested dict is updated."""
        data = {"data": {"nested": [0, {"dict": {"value": "found!"}}]}}
        path = ["data", "nested", 1, "dict", "value"]
        update(data, path, "Updated!")
        assert_that(find(data, path), equal_to("Updated!"))

    def test_update_existing_dict(self):
        """Tests if a value that is a dict is updated."""
        data = {"data": {"nested": [0, {"dict": {"value": [0, "found!"]}}]}}
        path = ["data", "nested", 1, "dict"]
        update(data, path, {"value": [13, 12, "Updated!"]})
        assert_that(
            find(data, path),
            has_entries({"value": contains_exactly(13, 12, "Updated!")}),
        )

    def test_update_existing_list(self):
        """Tests if a value that is a list is updated."""
        data = {"data": {"nested": [0, {"dict": {"value": [0, "found!"]}}]}}
        path = ["data", "nested", 1, "dict", "value"]
        update(data, path, [13, 12, "Updated!"])
        assert_that(find(data, path), contains_exactly(13, 12, "Updated!"))

    def test_update_non_existing(self):
        """Tests if the data structure is updated if the path does not exist in
        the initial structure.

        In the current example, the [1, "dict", "value", 2] part of the path
        does not exist, so data must be updated to:
        ```python
        {"data": {"nested": [None, {"dict": {"value": [None, None, "Created!"]]}}]}}
        ```

        The test passes if the value can be found after the update, there is no
        need to check the complete structure.
        """
        data = {"data": {"nested": []}}
        path = ["data", "nested", 1, "dict", "value", 2]
        update(data, path, "Created!")
        assert_that(find(data, path), equal_to("Created!"))

    def test_update_bad_list_path_on_scalar(self):
        """Tests if a PathError is raised if a list index reaches a leaf."""
        data = {"data": "bip"}
        path = ["data", 2]
        assert_that(calling(update).with_args(data, path, "boop"), raises(PathError))

    def test_update_bad_dict_path_on_scalar(self):
        """Tests if a PathError is raised if a key reaches a leaf."""
        data = {"data": "bip"}
        path = ["data", "key"]
        assert_that(calling(update).with_args(data, path, "boop"), raises(PathError))

    def test_update_bad_dict_path_on_root_list(self):
        """Tests if a PathError is raised if a key reaches the root list."""
        data = ["data", []]
        path = ["key", 1]
        assert_that(calling(update).with_args(data, path, "boop"), raises(PathError))

    def test_update_bad_dict_path_on_nested_list(self):
        """Tests if a PathError is raised if a key reaches a nested list."""
        data = {"data": []}
        path = ["data", "key"]
        assert_that(calling(update).with_args(data, path, "boop"), raises(PathError))


class TestNestedDataPathDelete(unittest.TestCase):
    """Tests for the delete method."""

    def test_delete_existing_value_in_list(self):
        """Tests if an index can be removed from a nested list."""
        data = {"data": {"nested": [0, {"dict": {"value": [-1, 0, "found!"]}}]}}
        path = ["data", "nested", 1, "dict", "value", 2]
        delete(data, path)
        assert_that(find(data, path[:-1]), contains_exactly(-1, 0))

    def test_delete_existing_value_in_dict(self):
        """Tests if a key can be removed from a nested dict."""
        data = {
            "data": {"nested": [0, {"dict": {"value": "found!", "other": "value"}}]}
        }
        path = ["data", "nested", 1, "dict", "value"]
        delete(data, path)
        assert_that(find(data, path[:-1]).items(), contains_exactly(("other", "value")))

    def test_delete_bad_list_path_on_scalar(self):
        """Tests if a PathError is raised if a list index reaches a leaf."""
        data = {"data": "bip"}
        path = ["data", 2]
        assert_that(calling(delete).with_args(data, path), raises(PathError))

    def test_delete_bad_dict_path_on_scalar(self):
        """Tests if a PathError is raised if a key reaches a leaf."""
        data = {"data": "bip"}
        path = ["data", "key"]
        assert_that(calling(delete).with_args(data, path), raises(PathError))

    def test_delete_bad_dict_path_on_root_list(self):
        """Tests if a PathError is raised if a key reaches the root list."""
        data = ["data", []]
        path = ["key", 1]
        assert_that(calling(delete).with_args(data, path), raises(PathError))

    def test_delete_bad_dict_path_on_nested_list(self):
        """Tests if a PathError is raised if a key reaches a nested list."""
        data = {"data": []}
        path = ["data", "key"]
        assert_that(calling(delete).with_args(data, path), raises(PathError))
