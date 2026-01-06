"""
Module providing the Generic() Class for connection on DB
"""

import uuid
from .error import Error, ErrorType


class DBConnector:  # pylint: disable=too-many-instance-attributes
    """Database Connector

    This is the way to save / store / retrieve objects

    :param ``**kwargs``:
        - *restriction=* ``func`` --
          not used yet


    """

    def __init__(self, **kwargs):
        """Constructor"""

        self.restriction_filter = kwargs.pop("restriction", None)

    def drop(self):  # pylint: disable=unused-argument
        """Drop the collection

        Mainly used in test


        :raise Error: Raise an error ErrorType.NOT_IMPLEMENTED or any db error
        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"drop is not implemented for {type(self)}",
        )

    def generate_id(self, o: dict) -> str:  # pylint: disable=unused-argument
        """
        The function to generate an Id.

        Mainly, not used, because the database itself do the job (like mongo).
        But for other cases, you must generate by yourself the uniq *_id* for the object

        :param o: The object given (json format)
        :type o: dict
        :return: an Id
        :rtype: str

        """
        return str(uuid.uuid4().int >> 64)

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        """Create the object into the DB and return the _id

        :param o: The object given (json format)
        :type o: dict
        :raise Error: Raise an error ErrorType.NOT_IMPLEMENTED or any db error

        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"create is not implemented for {type(self)}",
        )

    def save(self, _id: str, o: dict):  # pylint: disable=unused-argument
        """Save the objet

        :param _id: the _id of this object
        :type _id: str
        :param o: The object given (json format)
        :type o: dict
        :raise Error: Raise an error ErrorType.NOT_IMPLEMENTED or any db error

        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"save is not implemented for {type(self)}",
        )

    def get_by_id(self, _id: str) -> dict:  # pylint: disable=unused-argument
        """
        get an object by _id in the DB and return it

        :param _id: the _id
        :type _id: str
        :return: The object (json format)
        :rtype: dict
        :raise Error: Raise an error ErrorType.NOT_IMPLEMENTED or any db error

        """

        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"get_by_id is not implemented for {type(self)}",
        )

    def delete_by_id(self, _id: str):  # pylint: disable=unused-argument
        """The _id to delete on the db

        :param _id: the _id
        :type _id: str
        :raise Error: Raise an error ErrorType.NOT_IMPLEMENTED or any db error
        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"delete_by_id is not implemented for {type(self)}",
        )

    def select(
        self,
        select_filter,
        projection: dict = {},
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: dict = {},
    ):  # pylint: disable=unused-argument
        """
        Select from filter in the DB and return a list of dicts, with pagination

        :param select_filter: The filter for selection (depends on DB types)
        :param projection: The list of elements we want for each object
        :type projection: dict
        :param page_size: number of elements per page
        :type page_size: int
        :param num_of_element_to_skip: number of element to skip from beginning
        :type num_of_element_to_skip: int
        :param sort_object: Soon
        :type sort_object: dict
        :raise Error: Raise an error ErrorType.NOT_IMPLEMENTED or any db error

        """
        raise Error(
            ErrorType.NOT_IMPLEMENTED,
            f"select is not implemented for {type(self)}",
        )
