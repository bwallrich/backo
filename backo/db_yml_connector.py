"""
Module providing the Yml DB like
"""
# pylint: disable=logging-fstring-interpolation
import os
import yaml
from .db_connector import DBConnector
from .error import Error, ErrorType
from .log import log_system

log = log_system.get_or_create_logger("yml")


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

        if not os.path.exists( self._path ):
            os.mkdir(self._path)

        if not os.path.isdir( self._path ):
            raise Error(ErrorType.NOT_DIR, f'Yaml path "{self._path}" is not a directory.')
   


    def save(self, _id: str, o: dict):
        """
        Save the object
        """
        log.debug(f"save {_id} ")
        filename = os.path.join(self._path, _id + ".yml")

        log.debug(f"try to save {filename}")
        with open(filename, mode="w", encoding="utf8") as outfile:
            yaml.dump(o, outfile, default_flow_style=False)

    def create(self, o: dict):
        """
        Create the object into the DB and return the _id
        """
        _id = o["_id"]

        log.debug(f"create {_id} ")
        filename = os.path.join(self._path, _id + ".yml")

        if os.path.exists(filename):
            raise Error(ErrorType.ALREADYEXIST, f'_id "{_id}" already exists')

        log.debug(f"try to create {filename}")
        with open(filename, mode="w", encoding="utf8") as outfile:
            yaml.dump(o, outfile, default_flow_style=False)
        return _id

    def get_by_id(self, _id: str):
        """
        Read the corresponding file
        """
        log.debug(f"read {_id} ")
        filename = os.path.join(self._path, _id + ".yml")
        if not os.path.isfile(filename):
            raise Error(ErrorType.NOTFOUND, f'_id "{_id}" not found')

        log.debug(f"try to read {filename}")
        with open(filename, mode="r", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)
            return data_loaded

    def delete_by_id(self, _id: str):
        """
        Delete data by Id
        return True if deleted, or False if not found
        """
        log.debug(f"delete {_id}")
        filename = os.path.join(self._path, _id + ".yml")
        if os.path.isfile(filename):
            os.remove(filename)
            return True
        return False
