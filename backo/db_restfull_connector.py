"""
Module providing a generic REST API based database connector.
"""

# pylint: disable=logging-fstring-interpolation

from abc import abstractmethod
from typing import Callable
import requests
from stricto import Kparse

from .db_connector import DBConnector
from .error import NotFoundError, RestAPIError
from .log import log_system, LogLevel

log = log_system.get_or_create_logger("db-restfull-connector", LogLevel.DEBUG)


KPARSE_MODEL = {
    "host": {"type": str | None, "default": "localhost"},
    "port": {"type": int | None, "default": None},
    "tls": {"type": bool, "default": False},
    "validate_cert": {"type": bool, "default": True},
    "prefix": {"type": str, "default": "api/v1"},
    "username": {"type": str | None, "default": None},
    "password": {"type": str | None, "default": None},
    "auth_token": {"type": str | None, "default": None},
    "restriction": {"type": Callable, "default": None},
}

KPARSE_MODEL_ENDPOINT = {
    "endpoint": {"type": str | None, "default": ""},
    "method": {"type": str | None, "default": "GET"},
    "url_parameters": {"type": list | None, "default": []},
    "query_options": {"type": dict | None, "default": None},
    "data": {"type": dict | list | None, "default": None},
}


class DBRestfullConnector(DBConnector):
    """Abstract connector for read-oriented REST API backends.

    This connector stores common REST endpoint configuration and provides
    default behavior for write operations that are usually unavailable on
    public APIs.

    :param ``**kwargs``:
        - *host=* ``str`` -- The API host
        - *port=* ``int`` -- The API port
        - *tls=* ``bool`` -- Whether to use TLS (HTTPS) for API requests
        - *validate_cert=* ``bool`` -- Whether to validate TLS certificates (if TLS is
        - *prefix=* ``str`` -- Path prefix used for all endpoints
    """

    def __init__(self, **kwargs):
        options = Kparse(kwargs, KPARSE_MODEL)

        self._host = options.get("host")
        self._port = options.get("port")
        self._tls = options.get("tls")
        self._validate_cert = options.get("validate_cert")
        self._prefix = options.get("prefix")
        self._username = options.get("username")
        self._password = options.get("password")
        self._auth_token = options.get("auth_token")

        # Store the API base URI for use in endpoint methods
        self._uri = self._build_uri()

        DBConnector.__init__(self, **kwargs)

    def _build_uri(self) -> str:
        """Return the configured API base URI."""
        scheme = "https" if self._tls else "http"

        authentication = ""
        if self._username is not None:
            if self._password is not None:
                authentication = f"{self._username}:{self._password}@"
            else:
                authentication = f"{self._username}@"

        port = ""
        if self._port is not None:
            port = f":{self._port}"

        prefix = f"/{self._prefix.strip('/')}" if self._prefix else ""

        return f"{scheme}://{authentication}{self._host}{port}{prefix}"

    def _request(
        self,
        endpoint: str,
        url_parameters: list | tuple | None = None,
        query_options: dict | None = None,
        data: dict | list | None = None,
        method: str = "GET",
    ):
        """Execute an HTTP request on the configured REST endpoint.

        :param endpoint: endpoint name relative to ``self._uri``
        :type endpoint: str
        :param url_parameters: path parameters appended to endpoint
        :type url_parameters: list | tuple | None
        :param query_options: query string options appended after ``?``
        :type query_options: dict | None
        :param data: JSON payload for request body
        :type data: dict | list | None
        :param method: HTTP method (GET, POST, PUT, PATCH, DELETE...)
        :type method: str
        :return: tuple(status_code, parsed JSON response when possible, else response text)
        """
        endpoint = endpoint.strip("/") if endpoint else ""
        uri = self._uri
        if endpoint:
            uri = f"{uri}/{endpoint}"

        if url_parameters:
            encoded_parameters = [
                requests.utils.quote(str(parameter), safe="")
                for parameter in url_parameters
            ]
            uri = f"{uri}/{'/'.join(encoded_parameters)}"

        headers = {}
        if self._auth_token is not None:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        try:
            response = requests.request(
                method=method.upper(),
                url=uri,
                params=query_options,
                json=data,
                headers=headers,
                verify=self._validate_cert if self._tls else True,
                timeout=30,
            )
            response.raise_for_status()

            status_code = response.status_code

            if not response.text:
                return status_code, None

            try:
                return status_code, response.json()
            except ValueError:
                return status_code, response.text
        except requests.exceptions.HTTPError as http_error:
            raise RestAPIError(
                'REST request error "{0} {1}" ({2})',
                method.upper(),
                uri,
                http_error.response.status_code,
            ) from http_error
        except requests.exceptions.RequestException as request_error:
            raise RestAPIError(
                'REST connection error "{0} {1}": {2}',
                method.upper(),
                uri,
                request_error,
            ) from request_error

    @abstractmethod
    def drop(self, **kwargs):
        pass

    @abstractmethod
    def create(self, o: dict, **kwargs) -> str:  # pylint: disable=unused-argument
        pass

    @abstractmethod
    def save(self, _id: str, o: dict, **kwargs):  # pylint: disable=unused-argument
        pass

    def delete_by_id(self, _id: str, **kwargs) -> bool:
        options = Kparse(kwargs, KPARSE_MODEL_ENDPOINT)

        endpoint = options.get("endpoint")
        url_parameters = options.get("url_parameters")
        query_options = options.get("query_options")

        log.debug(
            "Delete %r from endpoint %r with url_parameters %r and query_options %r",
            _id,
            endpoint,
            url_parameters,
            query_options,
        )

        try:
            status_code, _ = self._request(
                endpoint=endpoint,
                url_parameters=url_parameters or [_id],
                query_options=query_options,
                method="DELETE",
            )
        except RestAPIError as e:
            status_code = None
            if len(e.args) > 0 and isinstance(e.args[-1], int):
                status_code = e.args[-1]

            if status_code == 404:
                raise NotFoundError('_id "{0}" not found', _id) from e

            if status_code is not None:
                raise RestAPIError(
                    'REST API returned status "{0}" for _id "{1}"',
                    status_code,
                    _id,
                    status_code,
                ) from e

            raise RestAPIError('REST API error while deleting _id "{0}"', _id) from e

        if status_code == 404:
            raise NotFoundError('_id "{0}" not found', _id)

        if status_code not in (200, 202, 204):
            raise RestAPIError(
                'REST API returned status "{0}" for _id "{1}"',
                status_code,
                _id,
                status_code,
            )

        return True

    def get_by_id(self, _id: str, **kwargs) -> dict:
        options = Kparse(kwargs, KPARSE_MODEL_ENDPOINT)

        endpoint = options.get("endpoint")
        url_parameters = options.get("url_parameters")
        query_options = options.get("query_options")

        log.debug(
            f"Get {_id} from endpoint {endpoint} with url_parameters {url_parameters} and query_options {query_options}"
        )
        try:
            status_code, data = self._request(
                endpoint=endpoint,
                url_parameters=url_parameters or [_id],
                query_options=query_options,
                method="GET",
            )
        except RestAPIError as e:
            status_code = None
            if len(e.args) > 0 and isinstance(e.args[-1], int):
                status_code = e.args[-1]

            if status_code == 404:
                raise NotFoundError('_id "{0}" not found', _id) from e

            if status_code is not None:
                raise RestAPIError(
                    'REST API returned status "{0}" for _id "{1}"',
                    status_code,
                    _id,
                    status_code,
                ) from e

            raise RestAPIError('REST API error while getting _id "{0}"', _id) from e

        if status_code == 404:
            raise NotFoundError('_id "{0}" not found', _id)

        if status_code != 200:
            raise RestAPIError(
                'REST API returned status "{0}" for _id "{1}"',
                status_code,
                _id,
            )

        if hasattr(self, "_clean_data"):
            self._clean_data(data)

        return data

    @abstractmethod
    def select(
        self,
        select_filter,
        projection: dict = {},
        page_size: int = 0,
        num_of_element_to_skip: int = 0,
        sort_object: dict = {},
        **kwargs,
    ) -> list:
        """See :func:`DBConnector.select`."""
