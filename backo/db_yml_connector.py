"""
Module providing the Yml DB like
"""
import os
import yaml
from .db_connector import DBConnector
from .error import Error, ErrorType


class DBYmlConnector(DBConnector):  # pylint: disable=too-many-instance-attributes
    """
    A generic type for a DB
    """

    def __init__(self, **kwargs):
        """
        available arguments
        """
        self._path = kwargs.pop("path", "/tmp")

        DBConnector.__init__(self, **kwargs)

    def generate_id(self, o):
        """
        Generate an _id before saving
        """
        return None

    def save(self, _id: str, obj: dict):
        """
        Save the object
        """
        filename = os.path.join(self._path, _id + ".yml")
        with open(filename, mode="w", encoding="utf8") as outfile:
            yaml.dump(obj, outfile, default_flow_style=False)

    def create(self, o: dict):
        """
        Create the object into the DB and return the _id
        """
        _id = o["_id"]
        filename = os.path.join(self._path, _id + ".yml")

        if os.path.exists(filename):
            raise Error(ErrorType.ALREADYEXIST, f'_id "{_id}" already exists')

        with open(filename, mode="w", encoding="utf8") as outfile:
            yaml.dump(o, outfile, default_flow_style=False)
        return _id

    def get_by_id(self, _id: str):
        """
        Read the corresponding file
        """
        filename = os.path.join(self._path, _id + ".yml")
        if not os.path.isfile(filename):
            raise Error(ErrorType.NOTFOUND, f'_id "{_id}" not found')

        with open(filename, mode="r", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)
            return data_loaded

    def delete_by_id(self, _id: str):
        """
        Delete data by Id
        """
        filename = os.path.join(self._path, _id + ".yml")
        if os.path.isfile(filename):
            os.remove(filename)
