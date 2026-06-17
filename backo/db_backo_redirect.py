"""
Module providing a generic REST API based database connector.
"""

import sys

# used for developpement
sys.path.insert(1, "../../stricto")

# pylint: disable=logging-fstring-interpolation
from .db_restfull_connector import DBRestfullConnector
from .error import DBError

from .log import log_system

log = log_system.get_or_create_logger("DBRedirect")


class DBRedirect(DBRestfullConnector):  # pylint: disable=too-many-instance-attributes
    """An example of a rest API connector"""

    _remote_collection: str = None

    def __init__(self, remote_collection: str, **kwargs):
        """constructor"""
        self._remote_collection = remote_collection
        DBRestfullConnector.__init__(self, **kwargs)

    def generate_id(self, o: dict) -> str:  # pylint: disable=unused-argument
        return o["_id"]

    def drop(self, **kwargs):  # pylint: disable=unused-argument
        raise DBError("DBRedirect doenst implement drop() method")

    def create(self, o: dict, **kwargs) -> str:  # pylint: disable=unused-argument
        return super().create(
            endpoint=self._remote_collection,
            o=o,
        )

    def save(self, _id: str, o: dict, **kwargs):  # pylint: disable=unused-argument
        return super().save(
            _id,
            endpoint=self._remote_collection,
            o=o,
        )

    def delete_by_id(self, _id: str, **kwargs):  # pylint: disable=unused-argument
        return super().delete_by_id(
            _id,
            endpoint=self._remote_collection,
        )

    def get_by_id(self, _id: str, **kwargs) -> dict:
        """See :func:`DBConnector.get_by_id`"""

        return super().get_by_id(
            _id,
            endpoint=self._remote_collection,
        )

    def select(
        self,
        select_filter,
        projection={},
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={"_id": 1},
        **kwargs
    ) -> list:
        """See :func:`DBConnector.select`

        Params ``select_filter`` and ``projection`` are not used

        """
        return super().select(
            select_filter,
            projection,
            page_size,
            num_of_element_to_skip,
            sort_object,
            endpoint=self._remote_collection,
            **kwargs
        )
