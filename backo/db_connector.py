"""
Module providing the Generic() Class for connection on DB
"""

import uuid
from .error import Error, ErrorType


class DBConnector:  # pylint: disable=too-many-instance-attributes
    """
    A generic type for a DB
    """

    def __init__(self, **kwargs):
        """
        available arguments

        restriction -> a function that must produce a filter (or None).
        """

        self.restriction_filter = kwargs.pop("restriction", None)

    def drop(self):  # pylint: disable=unused-argument
        """
        Drop the collection
        (used in test)
        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"drop is not implemented for {type(self)}",
        )

    def generate_id(self, o: dict):  # pylint: disable=unused-argument
        """
        generate an id:
        """
        return str(uuid.uuid4().int >> 64)

    def create(self, o: dict):  # pylint: disable=unused-argument
        """
        Create the object into the DB and return the _id
        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"create is not implemented for {type(self)}",
        )

    def save(self, _id: str, o: dict):  # pylint: disable=unused-argument
        """
        must be overwritten
        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"save is not implemented for {type(self)}",
        )

    def get_by_id(self, _id: str):  # pylint: disable=unused-argument
        """
        must be overwritten
        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"get_by_id is not implemented for {type(self)}",
        )

    def delete_by_id(self, _id: str):  # pylint: disable=unused-argument
        """
        must be overwritten
        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"delete_by_id is not implemented for {type(self)}",
        )

    def select(
        self,
        select_filter,
        projection={},
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={},
    ):  # pylint: disable=unused-argument
        """
        Select and return a list of dicts

        select_filter : The fiter
        projection : Fields whe want
        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"select is not implemented for {type(self)}",
        )
