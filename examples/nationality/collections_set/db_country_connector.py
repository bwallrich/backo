"""
Module using DBRestfullConnector to connect to restcountries.com API and retrieve country data.

Note: we assume that the signature of some inherited methods differ from the mother class
"""

# pylint: disable=logging-fstring-interpolation,arguments-differ
from backo import (
    DBRestfullConnector,
    log_system,
    LogLevel,
    DBError,
)

log = log_system.get_or_create_logger("wget", LogLevel.DEBUG)


class MyDBRestfullConnector(
    DBRestfullConnector
):  # pylint: disable=too-many-instance-attributes
    """An example of a rest API connector"""

    def __init__(self, **kwargs):
        """constructor"""
        DBRestfullConnector.__init__(
            self,
            host="www.apicountries.com",
            tls=True,
            prefix="countries",
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
        return o["alpha3Code"]

    def _clean_data(self, o: dict) -> dict:
        """clean data from unwanted informations

        :param o: the object
        :type o: dict
        """
        n = {}
        n["_id"] = self.generate_id(o)
        n["name"] = o["name"]
        n["flags"] = o["flags"]
        n["cca2"] = o["alpha2Code"]
        n["cca3"] = o["alpha3Code"]
        return n

    def drop(self):  # pylint: disable=unused-argument
        raise DBError("MyDBRestfullConnector doenst implement drop() method")

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        raise DBError("MyDBRestfullConnector doenst implement create() method")

    def save(self, _id: str, o: dict):  # pylint: disable=unused-argument
        raise DBError("MyDBRestfullConnector doenst implement save() method")

    def delete_by_id(self, _id: str):  # pylint: disable=unused-argument
        raise DBError("MyDBRestfullConnector doenst implement delete_by_id() method")

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        return super().get_by_id(
            _id,
            endpoint="alpha",
            query_options={"fields": "name,flags,cca2,cca3"},
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
            page_size,
            num_of_element_to_skip,
            sort_object,
            **kwargs,
        )
