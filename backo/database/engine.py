from .connection import DatabaseConnection
from .item import DatabaseItem


class DatabaseEngine:
    """The purpose of the DatabaseEngine is to perform requests
    to load DatabaseItems.

    Each operation (e.g. search()) is implemented using this procedure:

    1. ask the database_item for requests required to build the representation
       of the item associated to the given `_id`.
    3. perform those requests against the real database backend using the
       database_connection.
    4. provide the responses to the `database_item.load()` method so it can
       build a JSON-like dict representation of the `Item`.

    """

    def __init__(
        self, database_connection: DatabaseConnection, database_item: DatabaseItem
    ):
        """Creates a ready to operate DatabaseEngine.

        :param database_connection: Connection used to execute requests
        :param database_item: Specification of how to load item attributes from
        the database
        """
        self.database_connection = database_connection
        self.database_item = database_item

    def _execute_list_requests(self, requests_list, responses):
        for i in range(len(requests_list)):
            request = requests_list[i]
            if isinstance(request, dict):
                response = {}
                self._execute_nested_requests(request, response)
                responses.append(response)
            elif isinstance(request, list):
                response = []
                self._execute_list_requests(request, response)
                responses.append(response)
            else:
                responses.append(self.database_connection.execute_search(request))

    def _execute_nested_requests(self, requests_dict, responses):
        for key, value in requests_dict.items():
            if isinstance(value, dict):
                responses[key] = {}
                self._execute_nested_requests(value, responses[key])
            elif isinstance(value, list):
                responses[key] = []
                self._execute_list_requests(value, responses[key])
            else:
                responses[key] = self.database_connection.execute_search(value)

    def search(self, _id):
        """Search the database for an item with the given `_id`.

        The item is loaded and returned if found, else a NotFoundError is
        raised.

        :param _id: The backo `_id` of the item to retrieve from LDAP.
        """
        root_request, attribute_requests = self.database_item.search_request(_id)

        root_response = self.database_connection.execute_search(root_request)
        attribute_responses = None
        if isinstance(attribute_requests, dict):
            attribute_responses = {}
            self._execute_nested_requests(attribute_requests, attribute_responses)
        elif isinstance(attribute_requests, list):
            attribute_responses = []
            self._execute_list_requests(attribute_requests, attribute_responses)
        else:
            attribute_responses = self.database_connection.execute_search(
                attribute_requests
            )

        item = self.database_item.load(root_response, attribute_responses)
        item["_id"] = _id
        return item
