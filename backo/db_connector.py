"""
Module providing the Generic() Class for connection on DB
"""


class DBConnector:  # pylint: disable=too-many-instance-attributes
    """
    A generic type for a DB
    """

    def __init__(self, **kwargs):
        """
        available arguments
        """

    def create(self, o: dict):  # pylint: disable=unused-argument
        """
        Create the object into the DB and return the _id
        """
        return None

    def generate_id(self, o):  # pylint: disable=unused-argument
        """
        must be overwritten
        """
        return None

    def save(self, _id: str, obj: dict):  # pylint: disable=unused-argument
        """
        must be overwritten
        """

    def get_by_id(self, _id: str):  # pylint: disable=unused-argument
        """
        must be overwritten
        """

    def delete_by_id(self, _id: str):  # pylint: disable=unused-argument
        """
        must be overwritten
        """
