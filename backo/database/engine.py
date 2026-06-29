"""Implementation of the DatabaseEngine."""

from .connection import DatabaseConnection
from .item import DatabaseItem


class DatabaseEngine:
    """The purpose of the DatabaseEngine is to execute requests
    required to perform operations on DatabaseItems.

    Each operation (e.g. search()) is implemented using this procedure:

    1. ask the database_item for requests required to perform the operation
    3. execute those requests against the real database backend using the
       database_connection.
    4. provide the responses back to the `database_item` if required, e.g. to
    `load()` the JSON-like dict representation of the item

    """

    def __init__(
        self, database_connection: DatabaseConnection, database_item: DatabaseItem
    ):
        """Creates a ready to operate DatabaseEngine.

        :param database_connection: Connection used to execute requests
        :param database_item: Specificies how the item to manage is structured
        in the database.
        """
        self.database_connection = database_connection
        self.database_item = database_item
        self.database_item.set_default_connection(self.database_connection)

    def search(self, _id):
        """Search the database for an item with the given `_id`.

        Requests to execute come from database_item.search_request(). Responses
        are given back to the database_item.load() method to build the JSON-like
        dict representation of the item.

        :param _id: The ID of the item to search.
        :return: JSON-like dict representation of the item
        """
        base_request, attribute_requests = self.database_item.search_request(_id)

        base_response, attributes_responses = _execute_requests(
            base_request, attribute_requests, _execute_search
        )
        item = self.database_item.load(base_response, attributes_responses)
        item["_id"] = _id
        return item

    def create(self, item_value):
        """Creates a new item in the database.

        The item_value should match database_item.model specification so
        requests to execute can be built with database_item.create_request().

        The _id of the created item is returned. The nature of the _id is
        completely dependent of the item_mapper used by the database_item, but
        it is guaranteed that it is a string that can be later provided to
        search(), delete() or update() methods to work on the item.

        :param item_value: Initial values of attributes for the new item
        :return: ID of the created item
        """
        base_request, attributes_requests = self.database_item.create_request(
            item_value
        )

        base_response, _ = _execute_requests(
            base_request, attributes_requests, _execute_create
        )

        return self.database_item.created_id(base_response)

    def delete(self, _id):
        """Deletes the item associated to `_id` from the database.

        Requests to execute come from database_item.delete_request().

        This method does not return anything.

        :param _id: The ID of the item to delete.
        """
        base_request, attribute_requests = self.database_item.delete_request(_id)

        _execute_requests(base_request, attribute_requests, _execute_delete)

    def save(self, _id, item_value):
        """Updates the item associated to `_id` with the provided values.

        Requests to execute come from database_item.update_request().

        The item_value must contain all the attributes of the item, as if it was
        created.

        This method does not return anything.

        :param _id: The ID of the item to update.
        :param item_value: New values of attributes for the item
        """

        base_request, attribute_requests = self.database_item.update_request(
            _id, item_value
        )

        _execute_requests(base_request, attribute_requests, _execute_update)

    def select(self, item_filter):
        base_request, attribute_requests = self.database_item.select_request(
            item_filter
        )

        _execute_requests(base_request, attribute_requests, _execute_select)


def _execute_search(request):
    """Execute the search request using its own connection, that was set by the
    encapsulating DatabaseItem.
    """
    return request.connection.execute_search(request)


def _execute_create(request):
    """Execute the create request using its own connection, that was set by the
    encapsulating DatabaseItem.
    """
    return request.connection.execute_create(request)


def _execute_delete(request):
    """Execute the delete request using its own connection, that was set by the
    encapsulating DatabaseItem.
    """
    return request.connection.execute_delete(request)


def _execute_update(request):
    """Execute the update request using its own connection, that was set by the
    encapsulating DatabaseItem.
    """
    return request.connection.execute_update(request)


def _execute_select(request):
    """Execute the select request using its own connection, that was set by the
    encapsulating DatabaseItem.
    """
    return request.connection.execute_select(request)


def _execute_list_requests(requests_list, responses, request_method):
    """Execute the list of requests using the request_method, processing the
    nested structure as required.

    Responses are appended to the responses list so responses have the same
    shape as requests_list upon return.
    """
    for request in requests_list:
        if isinstance(request, dict):
            response = {}
            _execute_dict_requests(request, response, request_method)
            responses.append(response)
        elif isinstance(request, list):
            response = []
            _execute_list_requests(request, response, request_method)
            responses.append(response)
        elif request is not None:
            responses.append(request_method(request))
        else:
            responses.append(None)


def _execute_dict_requests(requests_dict, responses, request_method):
    """Execute the dict of requests using the request_method, processing the
    nested structure as required.

    Responses are inserted into the responses dict so responses have the same
    shape as requests_dict upon return.
    """
    for key, value in requests_dict.items():
        if isinstance(value, dict):
            responses[key] = {}
            _execute_dict_requests(value, responses[key], request_method)
        elif isinstance(value, list):
            responses[key] = []
            _execute_list_requests(value, responses[key], request_method)
        elif value is not None:
            responses[key] = request_method(value)
        else:
            responses[key] = None


def _execute_requests(base_request, attributes_requests, request_method):
    """Execute the base and attribute requests using request_method and returns
    responses as a tuple. Responses to attribute requests are returned in a
    structure with the same shape as attributes_requests.
    """
    base_response = request_method(base_request)
    attribute_responses = None
    if isinstance(attributes_requests, dict):
        attribute_responses = {}
        _execute_dict_requests(attributes_requests, attribute_responses, request_method)
    elif isinstance(attributes_requests, list):
        attribute_responses = []
        _execute_list_requests(attributes_requests, attribute_responses, request_method)
    elif attributes_requests is not None:
        attribute_responses = request_method(attributes_requests)
    return base_response, attribute_responses
