"""
Module providing a generic REST API based database connector.
"""

# pylint: disable=logging-fstring-interpolation

from abc import abstractmethod
from typing import Callable
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from stricto import Kparse

from .db_connector import DBConnector
from .error import NotFoundError, DBError
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
    """DBConnector for REST API backends.

    This connector allows complete interaction with other REST APIs.

    """

    def __init__(self, **kwargs):
        """

        :param ``**kwargs``:
            - *host=* ``str`` -- The API host
            - *port=* ``int`` -- The API port
            - *tls=* ``bool`` -- Whether to use TLS (HTTPS) for API requests
            - *validate_cert=* ``bool`` -- Whether to validate TLS certificates (if TLS is True)
            - *prefix=* ``str`` -- Path prefix used for all endpoints
            - *username=* ``str`` -- Username for basic authentication (optional)
            - *password=* ``str`` -- Password for basic authentication (optional)
            - *auth_token=* ``str`` -- Bearer token for authentication (optional)
            - *restriction=* ``Callable`` -- Restriction filter function (not implemented)

        """
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

        self._session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount(self._uri, adapter)
        self._session.mount(self._uri, adapter)

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
        :return: tuple(status_code, parsed JSON response when possible, else response text, Error or None)
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
            response = self._session.request(
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
                return status_code, None, None

            try:
                return status_code, response.json(), None
            except ValueError:
                return status_code, response.text, None

        except requests.exceptions.HTTPError as http_error:
            return http_error.response.status_code, None, http_error
        except requests.exceptions.RequestException as request_error:
            return None, None, request_error
        except Exception as e:  # pylint: disable=broad-exception-caught
            return None, None, e

    @abstractmethod
    def drop(self, **kwargs):
        """Drop the collection / table / resource (TO implement in subclasses)

        
        :param ``**kwargs``:
            - *endpoint=* ``str | None`` -- endpoint name relative to ``self._uri``
            - *method=* ``str | None`` -- HTTP method option from endpoint model \
                (ignored by create, which always uses ``POST``)
            - *url_parameters=* ``list | None`` -- path parameters appended to endpoint
            - *query_options=* ``dict | None`` -- query string options appended after ``?``
            - *data=* ``dict | None`` -- payload option from endpoint model (ignored by create,
                which uses ``o`` as request payload)
            - *username=* ``str`` -- Username for basic authentication (optional)
            - *password=* ``str`` -- Password for basic authentication (optional)
            - *auth_token=* ``str`` -- Bearer token for authentication (optional)
            - *restriction=* ``Callable`` -- Restriction filter function (not implemented)

        :return: True if the object was successfully deleted
        :rtype: bool
        :raise Error: Raise an error DBError, NotFoundError or any db error

        """

    def create(self, o: dict, **kwargs) -> str:  # pylint: disable=unused-argument
        """Create the object by issuing a POST request to the REST API and return the _id

        :param o: The object given (json format)
        :type o: dict
        :param kwargs: Endpoint options
        :type kwargs: dict
        :param kwargs.endpoint: endpoint name relative to ``self._uri``
        :type kwargs.endpoint: str | None
        :param kwargs.method: HTTP method option from endpoint model (ignored by create,
            which always uses ``POST``)
        :type kwargs.method: str | None
        :param kwargs.url_parameters: path parameters appended to endpoint
        :type kwargs.url_parameters: list | None
        :param kwargs.query_options: query string options appended after ``?``
        :type kwargs.query_options: dict | None
        :param kwargs.data: payload option from endpoint model (ignored by create,
            which uses ``o`` as request payload)
        :type kwargs.data: dict | list | None
        :return: the object _id
        :rtype: str
        :raise Error: Raise an error DBError, NotFoundError or any db error

        """
        options = Kparse(kwargs, KPARSE_MODEL_ENDPOINT)

        endpoint = options.get("endpoint")
        url_parameters = options.get("url_parameters")
        query_options = options.get("query_options")

        log.debug(
            "Create object on endpoint %r with url_parameters %r and query_options %r",
            endpoint,
            url_parameters,
            query_options,
        )

        status_code, data, error = self._request(
            endpoint=endpoint,
            url_parameters=url_parameters,
            query_options=query_options,
            data=o,
            method="POST",
        )

        if error is not None:
            if status_code == 404:
                raise NotFoundError(
                    'Create endpoint "{0}" not found', endpoint
                ) from error
            raise DBError('Endpoint "{0}" error', endpoint) from error

        if status_code == 404:
            raise NotFoundError('Create endpoint "{0}" not found', endpoint)

        if status_code not in (200, 201, 202):
            raise DBError(
                'REST API returned status "{0}" while creating object',
                status_code,
            )

        if isinstance(data, dict) and data.get("_id") is not None:
            return data.get("_id")

        raise DBError(
            "REST API create response does not contain _id",
        )

    def save(self, _id: str, o: dict, **kwargs):  # pylint: disable=unused-argument
        """Save / update the object by issuing a PUT request to the REST API and return the _id

        :param o: The object given (json format)
        :type o: dict
        :param kwargs: Endpoint options
        :type kwargs: dict
        :param kwargs.endpoint: endpoint name relative to ``self._uri``
        :type kwargs.endpoint: str | None
        :param kwargs.method: HTTP method option from endpoint model (ignored by create,
            which always uses ``POST``)
        :type kwargs.method: str | None
        :param kwargs.url_parameters: path parameters appended to endpoint
        :type kwargs.url_parameters: list | None
        :param kwargs.query_options: query string options appended after ``?``
        :type kwargs.query_options: dict | None
        :param kwargs.data: payload option from endpoint model (ignored by save,
            which uses ``o`` as request payload)
        :type kwargs.data: dict | list | None
        :return: True if the object was successfully saved/updated
        :rtype: bool
        :raise Error: Raise an error DBError, NotFoundError or any db error

        """
        options = Kparse(kwargs, KPARSE_MODEL_ENDPOINT)

        endpoint = options.get("endpoint")
        url_parameters = options.get("url_parameters")
        query_options = options.get("query_options")

        log.debug(
            "Update %r from endpoint %r with url_parameters %r and query_options %r",
            _id,
            endpoint,
            url_parameters,
            query_options,
        )

        status_code, _data, error = self._request(
            endpoint=endpoint,
            url_parameters=url_parameters or [_id],
            query_options=query_options,
            method="PUT",
            data=o,
        )

        if error is not None:
            if status_code == 404:
                raise NotFoundError('_id "{0}" not found', _id) from error
            log.error(error)
            raise DBError('Endpoint "{0}" error', endpoint) from error

        if status_code == 404:
            raise NotFoundError('_id "{0}" not found', _id)

        if status_code not in (200, 201, 202):
            raise DBError(
                'REST API returned status "{0}" while saving object "{1}',
                status_code,
                _id,
            )

    def delete_by_id(self, _id: str, **kwargs) -> bool:
        """Delete the object by issuing a DELETE request to the REST API

        :param _id: The object _id to delete
        :type _id: str
        :param kwargs: Endpoint options
        :type kwargs: dict
        :param kwargs.endpoint: endpoint name relative to ``self._uri``
        :type kwargs.endpoint: str | None
        :param kwargs.method: HTTP method option from endpoint model (ignored by create,
            which always uses ``POST``)
        :type kwargs.method: str | None
        :param kwargs.url_parameters: path parameters appended to endpoint
        :type kwargs.url_parameters: list | None
        :param kwargs.query_options: query string options appended after ``?``
        :type kwargs.query_options: dict | None
        :param kwargs.data: payload option from endpoint model (ignored by save,
            which uses ``o`` as request payload)
        :type kwargs.data: dict | list | None
        :return: True if the object was successfully deleted
        :rtype: bool
        :raise Error: Raise an error DBError, NotFoundError or any db error

        """
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

        status_code, _data, error = self._request(
            endpoint=endpoint,
            url_parameters=url_parameters or [_id],
            query_options=query_options,
            method="DELETE",
        )

        if error is not None:
            if status_code == 404:
                raise NotFoundError('_id "{0}" not found', _id) from error
            raise DBError('Endpoint "{0}" error', endpoint) from error

        if status_code == 404:
            raise NotFoundError('_id "{0}" not found', _id)

        if status_code not in (200, 202, 204):
            raise DBError(
                'REST API returned status "{0}" while saving object "{1}',
                status_code,
                _id,
            )

    def get_by_id(self, _id: str, **kwargs) -> dict:
        """Get the objectby its _id by issuing a GET request to the REST API

        :param _id: The object _id to get
        :type _id: str
        :param kwargs: Endpoint options
        :type kwargs: dict
        :param kwargs.endpoint: endpoint name relative to ``self._uri``
        :type kwargs.endpoint: str | None
        :param kwargs.method: HTTP method option from endpoint model (ignored by create,
            which always uses ``POST``)
        :type kwargs.method: str | None
        :param kwargs.url_parameters: path parameters appended to endpoint
        :type kwargs.url_parameters: list | None
        :param kwargs.query_options: query string options appended after ``?``
        :type kwargs.query_options: dict | None
        :param kwargs.data: payload option from endpoint model (ignored by save,
            which uses ``o`` as request payload)
        :type kwargs.data: dict | list | None
        :return: the object corresponding to the _id
        :rtype: dict
        :raise Error: Raise an error DBError, NotFoundError or any db error

        """
        options = Kparse(kwargs, KPARSE_MODEL_ENDPOINT)

        endpoint = options.get("endpoint")
        url_parameters = options.get("url_parameters")
        query_options = options.get("query_options")

        log.debug(
            f"Get {_id} from endpoint {endpoint} with url_parameters {url_parameters} and query_options {query_options}"
        )
        status_code, data, error = self._request(
            endpoint=endpoint,
            url_parameters=url_parameters or [_id],
            query_options=query_options,
            method="GET",
        )

        if error is not None:
            if status_code == 404:
                raise NotFoundError('_id "{0}" not found', _id) from error
            raise DBError('Endpoint "{0}" error', endpoint) from error

        if status_code == 404:
            raise NotFoundError('_id "{0}" not found', _id)

        if status_code != 200:
            raise DBError(
                'REST API returned status "{0}" while getting object "{1}',
                status_code,
                _id,
            )

        if hasattr(self, "_clean_data"):
            return self._clean_data(data)

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
        """
        Select from filter in the DB and return a list of dicts, with pagination (TO implement in subclasses)

        :param select_filter: The filter for selection (depends on DB types)
        :param projection: The list of elements we want for each object
        :type projection: dict
        :param page_size: number of elements per page
        :type page_size: int
        :param num_of_element_to_skip: number of element to skip from beginning
        :type num_of_element_to_skip: int
        :param sort_object: Soon
        :type sort_object: dict
        :param kwargs: Endpoint options
        :type kwargs: dict
        :param kwargs.endpoint: endpoint name relative to ``self._uri``
        :type kwargs.endpoint: str | None
        :param kwargs.method: HTTP method option from endpoint model (ignored by create,
            which always uses ``POST``)
        :type kwargs.method: str | None
        :param kwargs.url_parameters: path parameters appended to endpoint
        :type kwargs.url_parameters: list | None
        :param kwargs.query_options: query string options appended after ``?``
        :type kwargs.query_options: dict | None
        :param kwargs.data: payload option from endpoint model (ignored by save,
            which uses ``o`` as request payload)
        :type kwargs.data: dict | list | None
        :return: list of objects matching the selection filter
        :rtype: list
        :raise Error: Raise an error DBError or any db error

        """

        options = Kparse(kwargs, KPARSE_MODEL_ENDPOINT)

        endpoint = options.get("endpoint")

        status_code, data, error = self._request(
            endpoint=endpoint,
            url_parameters=options.get("url_parameters"),
            query_options=options.get("query_options"),
            method="GET",
        )

        if error is not None:
            if status_code == 404:
                raise NotFoundError('Endpoint "{0}" not found', endpoint) from error
            raise DBError('Endpoint "{0}" error', endpoint) from error

        if status_code == 404:
            raise NotFoundError('selection error "{0}"', status_code)

        if status_code != 200:
            raise DBError('selection error "{0}"', status_code)

        if data is None:
            return []

        if isinstance(data, list):
            if hasattr(self, "_clean_data"):
                r = []
                for d in data:
                    r.append(self._clean_data(d))
                return r
            return data

        if isinstance(data, dict):
            if "result" in data and isinstance(data["result"], list):
                if hasattr(self, "_clean_data"):
                    r = []
                    for d in data["result"]:
                        r.append(self._clean_data(d))
                    return r

                return data["result"]

        raise DBError('select endpoint "{0}" return non understandable dict', endpoint)
