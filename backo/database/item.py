"""Implementation of the DatabaseItem"""

from .mapper import ItemMapper


def _set_requests_connection(requests, connection):
    if isinstance(requests, list):
        for request in requests:
            _set_requests_connection(request, connection)
    elif isinstance(requests, dict):
        for request in requests.values():
            _set_requests_connection(request, connection)
    else:
        requests.connection = connection


def _requests_with_connection(requests, connection):
    _set_requests_connection(requests, connection)
    return requests


def _search_request(attribute, base_request, _id):
    return _requests_with_connection(
        attribute.search_request(base_request, _id), attribute.connection
    )


def _create_request(attribute, base_request, value):
    return _requests_with_connection(
        attribute.create_request(base_request, value), attribute.connection
    )


def _delete_request(attribute, base_request, _id):
    return _requests_with_connection(
        attribute.delete_request(base_request, _id), attribute.connection
    )


def _update_request(attribute, base_request, _id, value):
    return _requests_with_connection(
        attribute.update_request(base_request, _id, value), attribute.connection
    )


class DatabaseItem:
    """A DatabaseItem specifies how data should be loaded from the database to
    produce a valid JSON-like dict that could be provided to load a backo Item.

    Even if its structure might look similar to the associated backo Item, it is
    not a duplication of information contained in the backo Item, as the purpose
    of the DatabaseItem is only to specify how to produce a valid JSON-like dict
    from raw items contained in the database.

    The Item specifies the structure of the object with fields and types, and the
    DatabaseItem specifies how to retrieve them from a specific database.
    """

    def __init__(self, item_mapper: ItemMapper, model):
        """
        The `item_mapper` specifies how to build base requests for each
        operation. Each attribute of the model is then allowed to modify the
        base request en retrieve data from its response, in addition to their
        own requests.

        The `model` is a dict mapping JSON fields to specification of database
        attributes. Here is a simple example for LDAP:
        ```
        {
            "name": Attribute("uid"),
            "description": Attribute("description")
        }
        ```
        With this example, the DatabaseItem will load() the JSON-like dict by
        loading values of `name` and `description` fields from the `uid` and
        `description` attributes of the LDAP entry associated to the item. The
        `item_mapper` (e.g. `MapByDN`) defined how to retrieve the entry itself.

        :param item_mapper: Specifies how to map database entries to backo `_id`s.
        :param model: Dictionnary of database attributes
        """
        self.item_mapper = item_mapper
        self.model = model

        # Informs each attribute of its path within the model
        self._set_attribute_paths(self.model, [])

        # It is set by the DatabaseEngine using
        # set_default_connection
        self.connection = None

    def _set_attribute_paths(self, attributes, current_path):
        if isinstance(attributes, list):
            i = 0
            for attribute in attributes:
                self._set_attribute_paths(attribute, current_path + [i])
                i += 1
        elif isinstance(attributes, dict):
            for key, attribute in attributes.items():
                self._set_attribute_paths(attribute, current_path + [key])
        else:
            attributes.set_attribute_path(current_path)

    def set_default_connection(self, connection):
        """Sets the connection that will be used to perform base requests and
        attribute requests, unless the attribute is already associated to a
        specific connection.
        """
        self.connection = connection
        self._set_default_connection(self.model, connection)

    def _set_default_connection(self, attributes, connection):
        if isinstance(attributes, list):
            for attribute in attributes:
                self._set_default_connection(attribute, connection)
        elif isinstance(attributes, dict):
            for attribute in attributes.values():
                self._set_default_connection(attribute, connection)
        else:
            attributes.set_default_connection(connection)

    def _request_list(
        self, base_request, request_list, attributes_list, _id, request_method
    ):
        for attribute in attributes_list:
            if isinstance(attribute, list):
                requests = []
                self._request_list(
                    base_request, requests, attribute, _id, request_method
                )
                request_list.append(requests)
            elif isinstance(attribute, dict):
                requests = {}
                self._request_dict(
                    base_request, requests, attribute, _id, request_method
                )
                request_list.append(requests)
            else:
                request_list.append(request_method(attribute, base_request, _id))

    def _request_dict(
        self, base_request, request_dict, attributes_dict, _id, request_method
    ):
        for key, attribute in attributes_dict.items():
            if isinstance(attribute, list):
                requests = []
                self._request_list(
                    base_request, requests, attribute, _id, request_method
                )
                request_dict[key] = requests
            elif isinstance(attribute, dict):
                requests = {}
                self._request_dict(
                    base_request, requests, attribute, _id, request_method
                )
                request_dict[key] = requests
            else:
                request_dict[key] = request_method(attribute, base_request, _id)

    def _request_list_with_values(
        self, base_request, request_list, attributes_list, values, request_method
    ):
        for attribute, value in zip(attributes_list, values):
            if isinstance(attribute, list):
                requests = []
                self._request_list_with_values(
                    base_request, requests, attribute, value, request_method
                )
                request_list.append(requests)
            elif isinstance(attribute, dict):
                requests = {}
                self._request_dict_with_values(
                    base_request, requests, attribute, value, request_method
                )
                request_list.append(requests)
            else:
                request_list.append(request_method(attribute, base_request, value))

    def _request_dict_with_values(
        self, base_request, request_dict, attributes_dict, values, request_method
    ):
        for (key, attribute), value in zip(attributes_dict.items(), values.values()):
            if isinstance(attribute, list):
                requests = []
                self._request_list_with_values(
                    base_request, requests, attribute, value, request_method
                )
                request_dict[key] = requests
            elif isinstance(attribute, dict):
                requests = {}
                self._request_dict_with_values(
                    base_request, requests, attribute, value, request_method
                )
                request_dict[key] = requests
            else:
                request_dict[key] = request_method(attribute, base_request, value)

    def _request_list_with_id_and_values(
        self, base_request, request_list, attributes_list, _id, values, request_method
    ):
        for attribute, value in zip(attributes_list, values):
            if isinstance(attribute, list):
                requests = []
                self._request_list_with_id_and_values(
                    base_request, requests, attribute, _id, value, request_method
                )
                request_list.append(requests)
            elif isinstance(attribute, dict):
                requests = {}
                self._request_dict_with_id_and_values(
                    base_request, requests, attribute, _id, value, request_method
                )
                request_list.append(requests)
            else:
                request_list.append(request_method(attribute, base_request, _id, value))

    def _request_dict_with_id_and_values(
        self, base_request, request_dict, attributes_dict, _id, values, request_method
    ):
        for (key, attribute), value in zip(attributes_dict.items(), values.values()):
            if isinstance(attribute, list):
                requests = []
                self._request_list_with_id_and_values(
                    base_request, requests, attribute, _id, value, request_method
                )
                request_dict[key] = requests
            elif isinstance(attribute, dict):
                requests = {}
                self._request_dict_with_id_and_values(
                    base_request, requests, attribute, _id, value, request_method
                )
                request_dict[key] = requests
            else:
                request_dict[key] = request_method(attribute, base_request, _id, value)

    def search_request(self, _id):
        """Builds a set of search requests that will be able to load all the
        attributes required to load the item represented by `_id`.

        Responses obtained by the DatabaseEngine will then be passed to the
        load() method of the DatabaseItem.

        :param _id: ID of the item to search
        """

        # Builds request required by the `item_mapper` to perform the `base`
        # initialization of the `DatabaseItem` instance associated to an `_id`
        base_request = self.item_mapper.search_request(_id)
        base_request.connection = self.connection

        #  Builds additional requests required to initialize all attributes of
        #  the `model`. Each attribute is allowed to either modify the
        #  `base_request`, build new requests or do nothing.
        model_requests = None
        if isinstance(self.model, dict):
            model_requests = {}
            self._request_dict(
                base_request, model_requests, self.model, _id, _search_request
            )
        elif isinstance(self.model, list):
            model_requests = []
            self._request_list(
                base_request, model_requests, self.model, _id, _search_request
            )
        else:
            model_requests = _search_request(self.model, base_request, _id)

        return base_request, model_requests

    def create_request(self, item_value):
        """Builds a set of create requests that will be able to load all the
        attributes required to load the item represented by `_id`.

        Responses obtained by the DatabaseEngine will then be passed to the
        created_id() method of the DatabaseItem.

        :param item_value: JSON-like dict with values of attributes of the new
        item. Its structure must be compatible with the model.
        """

        # Builds request required by the `item_mapper` to create the `item` with
        # value `item_value` and initialize its _id
        base_request = self.item_mapper.create_request(item_value)
        base_request.connection = self.connection

        #  Builds additional requests required to create all attributes of the
        #  `model`. Each attribute is allowed to either modify the
        #  `base_request`, build a new request or do nothing.
        model_requests = None
        if isinstance(self.model, dict):
            model_requests = {}
            self._request_dict_with_values(
                base_request, model_requests, self.model, item_value, _create_request
            )
        elif isinstance(self.model, list):
            model_requests = []
            self._request_list_with_values(
                base_request, model_requests, self.model, item_value, _create_request
            )
        else:
            model_requests = _create_request(self.model, base_request,
                                             item_value)

        return base_request, model_requests

    def delete_request(self, _id):
        """Builds a set of delete requests that will be able to delete all the
        attributes of the item represented by `_id` (and the item itself).

        :param _id: ID of the item to delete
        """

        # Builds request required by the `item_mapper` to delete the item
        # corresponding to _id
        base_request = self.item_mapper.delete_request(_id)
        base_request.connection = self.connection

        #  Builds additional requests required to delete all attributes of the
        #  `DatabaseItem`. Each attribute is allowed to either modify the
        #  `base_request`, build a new request or do nothing.
        model_requests = None
        if isinstance(self.model, dict):
            model_requests = {}
            self._request_dict(
                base_request, model_requests, self.model, _id, _delete_request
            )
        elif isinstance(self.model, list):
            model_requests = []
            self._request_list(
                base_request, model_requests, self.model, _id, _delete_request
            )
        else:
            model_requests = _delete_request(self.model, base_request, _id)

        return base_request, model_requests

    def update_request(self, _id, item_value):
        """Builds a set of update requests that will be able to update the
        attributes of the item represented by `_id` with values from
        `item_value`.

        :param _id: ID of the item to update
        :param item_value: JSON-like dict with values of attributes of the new
        item. Its structure must be compatible with the model.
        """

        # Builds request required by the `item_mapper` to create the `item` with
        # value `item_value` and initialize its _id
        base_request = self.item_mapper.update_request(_id, item_value)
        base_request.connection = self.connection

        #  Builds additional requests required to create all attributes of the
        #  `model`. Each attribute is allowed to either modify the
        #  `base_request`, build a new request or do nothing.
        model_requests = None
        if isinstance(self.model, dict):
            model_requests = {}
            self._request_dict_with_id_and_values(
                base_request, model_requests, self.model, _id, item_value, _update_request
            )
        elif isinstance(self.model, list):
            model_requests = []
            self._request_list_with_id_and_values(
                base_request, model_requests, self.model, _id, item_value, _update_request
            )
        else:
            model_requests = _update_request(self.model, base_request,
                                             _id, item_value)

        return base_request, model_requests

    def _load_list(
        self, base_request_response, attributes_responses, item_list, attributes_list
    ):
        for attribute, response in zip(attributes_list, attributes_responses):
            if isinstance(attribute, dict):
                item_value = {}
                self._load_dict(
                    base_request_response,
                    response,
                    item_value,
                    attribute,
                )
                item_list.append(item_value)
            elif isinstance(attribute, list):
                item_value = []
                self._load_list(
                    base_request_response,
                    response,
                    item_value,
                    attribute,
                )
                item_list.append(item_value)
            else:
                item_list.append(attribute.load(base_request_response, response))

    def _load_dict(
        self, base_request_response, attributes_responses, item_node, attributes_node
    ):
        for key, attribute in attributes_node.items():
            if isinstance(attribute, dict):
                item_node[key] = {}
                self._load_dict(
                    base_request_response,
                    attributes_responses[key],
                    item_node[key],
                    attribute,
                )
            elif isinstance(attribute, list):
                item_node[key] = []
                self._load_list(
                    base_request_response,
                    attributes_responses[key],
                    item_node[key],
                    attribute,
                )
            else:
                item_node[key] = attributes_node[key].load(
                    base_request_response, attributes_responses[key]
                )

    def load(self, base_request_response, attribute_responses):
        """Loads the item in a JSON-like dict from the database response.

        The response as been obtained by the DatabaseEngine from the request provided by
        search_request().

        The returned value is a JSON-like dict that can be used later to load a
        backo item using `item.load(loaded_json_dict)`.

        Notice the `_id` is not yet included in the result, as it only includes
        values retrieved using the `model`.
        """
        item = self.item_mapper.load(base_request_response)

        if isinstance(self.model, list):
            self._load_list(base_request_response, attribute_responses, item, self.model)
        elif isinstance(self.model, dict):
            self._load_dict(base_request_response, attribute_responses, item, self.model)
        else:
            item = self.model.load(base_request_response, attribute_responses)
        return item

    def created_id(self, base_create_response):
        """Returns the value that should be used as _id from the response of the
        create operation.
        """
        return self.item_mapper.created_id(base_create_response)
