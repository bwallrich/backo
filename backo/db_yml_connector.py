"""
Module providing the Yml DB like
"""

# pylint: disable=logging-fstring-interpolation
import os
import sys
import re
import yaml

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Kparse

from .db_connector import DBConnector
from .error import NotFoundError, DBError
from .log import log_system


KPARSE_MODEL = {"path": {"type": str, "default": "/tmp"}}

log = log_system.get_or_create_logger("yml")


class DBYmlConnector(DBConnector):  # pylint: disable=too-many-instance-attributes
    """Yaml files database Connector

    This is the way to save / store / retrieve objects in yaml files

    :param ``**kwargs``:
        - *path=* ``str`` -- The directory to store yaml files


    """

    def __init__(self, **kwargs):
        """constructor"""

        options = Kparse(kwargs, KPARSE_MODEL)

        self._path = options.get("path")

        DBConnector.__init__(self, **kwargs)

        if not os.path.exists(self._path):
            os.makedirs(self._path)

        if not os.path.isdir(self._path):
            raise DBError('Yaml path "{0}" is not a directory', self._path)

        if self.restriction_filter is not None:
            raise DBError("Restriction filter not implemented for yml")

    def drop(self) -> None:
        """See :func:`DBConnector.drop`"""
        dirs = os.listdir(self._path)
        for file in dirs:
            if re.match(r".*\.yml$", file):
                os.unlink(os.path.join(self._path, file))

    def save(self, _id: str, o: dict) -> None:
        """See :func:`DBConnector.save`"""
        log.debug(f"save {_id} ")
        filename = os.path.join(self._path, _id + ".yml")

        log.debug(f"try to save {filename}")
        with open(filename, mode="w", encoding="utf-8") as outfile:
            yaml.dump(o, outfile, default_flow_style=False)

    def create(self, o: dict) -> str:
        """See :func:`DBConnector.create`"""
        _id = o["_id"]

        log.debug(f"create {_id} ")
        filename = os.path.join(self._path, _id + ".yml")

        if os.path.exists(filename):
            raise DBError('_id "{0}" already exist in path "{1}"', _id, self._path)

        log.debug(f"try to create {filename}")
        with open(filename, mode="w", encoding="utf-8") as outfile:
            yaml.dump(o, outfile, default_flow_style=False)
        return _id

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        log.debug(f"read {_id} ")

        filename = os.path.join(self._path, _id + ".yml")
        if not os.path.isfile(filename):
            raise NotFoundError('_id "{0}" not found in path "{1}"', _id, self._path)

        log.debug(f"try to read {filename}")
        with open(filename, mode="r", encoding="utf-8") as stream:
            data_loaded = yaml.safe_load(stream)
            return data_loaded

    def delete_by_id(self, _id: str) -> bool:
        """See :func:`DBConnector.delete_by_id`"""
        log.debug(f"delete {_id}")
        filename = os.path.join(self._path, _id + ".yml")
        if os.path.isfile(filename):
            os.remove(filename)
            return True
        return False

    def select(
        self,
        select_filter,
        projection={},
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={"_id": 1},
    ) -> list:
        """See :func:`DBConnector.select`

        Params ``select_filter`` and ``projection`` are not used

        """
        log.debug(
            "select(%r, %r).sort(%r).skip(%r).limit(%r)",
            select_filter,
            projection,
            sort_object,
            num_of_element_to_skip,
            page_size,
        )

        try:
            result_list = []
            dirs = os.listdir(self._path)
            for file in dirs:
                if not re.match(r".*\.yml$", file):
                    continue

                with open(
                    os.path.join(self._path, file), mode="r", encoding="utf-8"
                ) as stream:
                    data_loaded = yaml.safe_load(stream)
                result_list.append(data_loaded)
        except Exception as e:
            raise DBError('Error while select in path "{0}"', self._path) from e

        return result_list
