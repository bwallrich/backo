"""
Module using DBRestfullConnector to connect to restcountries.com API and retrieve country data.

Note: we assume that the signature of some inherited methods differ from the mother class
"""

# pylint: disable=logging-fstring-interpolation,arguments-differ
from backo import (
    DBRestfullConnector,
    log_system,
    LogLevel,
    NotFoundError,
    DBError,
    RestAPIError,
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
            host="restcountries.com",
            tls=True,
            prefix="v3.1",
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
        return o["cca3"]

    def _clean_data(self, o: dict) -> None:
        """clean data from unwanted informations

        :param o: the object
        :type o: dict
        """
        del o["name"]["nativeName"]
        o["_id"] = self.generate_id(o)

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
        try:
            return super().get_by_id(
                _id,
                endpoint="alpha",
                query_options={"fields": "name,flags,cca2,cca3"},
            )
        except RestAPIError as e:
            # restcountries.com returns a 400 - Bad request when a country is not found, so we consider that as a NotFoundError
            status_code = None
            if len(e.args) > 0 and isinstance(e.args[-1], int):
                status_code = e.args[-1]
            if status_code == 400:
                raise NotFoundError('_id "{0}" not found', _id) from e
            raise e

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
            status_code, list_of_countries = self._request(
                endpoint="all",
                query_options={"fields": "name,flags,cca2,cca3"},
                method="GET",
            )
        except RestAPIError as e:
            # restcountries.com may return 400 for invalid request parameters.
            status_code = None
            if len(e.args) > 0 and isinstance(e.args[-1], int):
                status_code = e.args[-1]
            if status_code == 400:
                raise NotFoundError('selection error country "{0}"', status_code) from e
            raise e

        if status_code == 404:
            raise NotFoundError('selection error country "{0}"', status_code)

        if status_code != 200:
            raise RestAPIError(
                'REST API returned status "{0}" for countries selection',
                status_code,
                status_code,
            )

        if list_of_countries is None:
            return []

        for c in list_of_countries:
            self._clean_data(c)

        return list_of_countries
