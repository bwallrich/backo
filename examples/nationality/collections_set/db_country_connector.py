"""
Module providing the Yml DB like
"""

# pylint: disable=logging-fstring-interpolation
import json
import http.client
from backo import DBConnector, log_system, LogLevel, Error, ErrorType

log = log_system.get_or_create_logger("wget", LogLevel.DEBUG)


class MyDBRestfullConnector(
    DBConnector
):  # pylint: disable=too-many-instance-attributes
    """An example of a rest API connector"""

    def __init__(self, **kwargs):
        """constructor"""
        self._prefix = "https://restcountries.com/v3.1"
        self._host = "restcountries.com"

        DBConnector.__init__(self, **kwargs)

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

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        log.debug(f"wget {_id} ")
        connection = http.client.HTTPSConnection(self._host)
        connection.request("GET", f"/v3.1/alpha/{_id}?fields=name,flags,cca2,cca3")
        response = connection.getresponse()
        if response.status == 200:
            data_string = response.read().decode()
            log.debug(f"wget {_id} got {data_string}")

            data = json.loads(data_string)

            # Clean datas
            self._clean_data(data)
            connection.close()
            return data

        connection.close()
        raise Error(
            ErrorType.NOTFOUND,
            f'country _id "{_id}" not found {response.status}/{response.reason}',
        )

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

        connection = http.client.HTTPSConnection(self._host)
        connection.request("GET", "/v3.1/all?fields=name,flags,cca2,cca3")
        response = connection.getresponse()
        if response.status == 200:
            data_string = response.read().decode()
            connection.close()
            list_of_countries = json.loads(data_string)

            for c in list_of_countries:
                self._clean_data(c)

            return list_of_countries

        connection.close()
        raise Error(
            ErrorType.NOTFOUND,
            f"country selection error {response.status}/{response.reason}",
        )
