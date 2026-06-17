"""
Module using DBRestfullConnector to connect to the Hypervisor REST API

Note: we assume that the signature of some inherited methods differ from the mother class
"""

# pylint: disable=logging-fstring-interpolation,arguments-differ
from backo import (
    DBRestfullConnector,
    log_system,
    LogLevel,
    DBError,
)

log = log_system.get_or_create_logger("vms-connector", LogLevel.DEBUG)


class VMsConnector(DBRestfullConnector):  # pylint: disable=too-many-instance-attributes
    """An example of a rest API connector"""

    def __init__(self, **kwargs):
        """constructor"""
        DBRestfullConnector.__init__(
            self,
            host="localhost",
            port=12345,
            tls=False,
            prefix="api/v1/hypervisor",
            **kwargs,
        )

    def generate_id(self, o: dict) -> str:  # pylint: disable=unused-argument
        """
        The function to generate an Id.

        :param o: The object given (json format)
        :type o: dict
        :return: an Id
        :rtype: str

        """
        return o["_id"]

    def drop(self):  # pylint: disable=unused-argument
        raise DBError("VMsConnector doenst implement drop() method")

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        return super().create(
            endpoint="vms",
            o=o,
        )

    def save(self, _id: str, o: dict):  # pylint: disable=unused-argument
        return super().save(
            _id,
            endpoint="vms",
            o=o,
        )

    def delete_by_id(self, _id: str):  # pylint: disable=unused-argument
        return super().delete_by_id(
            _id,
            endpoint="vms",
        )

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        return super().get_by_id(
            _id,
            endpoint="vms",
        )

    def select(
        self,
        select_filter,
        projection={},
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={"_id": 1},
        **kwargs,
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

        return super().select(
            select_filter,
            projection,
            sort_object,
            num_of_element_to_skip,
            page_size,
            endpoint="vms",
            method="GET",
        )
