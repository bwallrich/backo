from abc import ABC, abstractmethod
from .request import DatabaseSearchRequest, DatabaseCreateRequest, DatabaseDeleteRequest
from typing import Any


class IdMapper(ABC):
    @abstractmethod
    def id(self, response) -> str:
        pass

    @abstractmethod
    def search_request(self, _id) -> DatabaseSearchRequest:
        pass

    @abstractmethod
    def create_request(self, item_value) -> DatabaseCreateRequest:
        pass

    @abstractmethod
    def delete_request(self, _id) -> DatabaseDeleteRequest:
        pass

    @abstractmethod
    def update_request(self, _id, item_value) -> DatabaseDeleteRequest:
        pass

    def load(self, _base_response):
        return {}


def _search_request(attribute, base_request, _id):
    return attribute.search_request(base_request, _id)


def _create_request(attribute, base_request, value):
    return attribute.create_request(base_request, value)


def _delete_request(attribute, base_request, _id):
    return attribute.delete_request(base_request, _id)


def _update_request(attribute, base_request, _id, value):
    return attribute.update_request(base_request, _id, value)


class DatabaseItem:
    """A DatabaseItem specifies how data should be loaded from the database to
    produce a valid JSON that could be provided to load a backo Item.

    Even if its structure might look similar to the associated backo Item, it is
    not a duplication of information contained in the backo Item, as the purpose
    of the DatabaseItem is only to specify how to produce a valid JSON-like dict
    from raw items contained in the database.

    The Item specifies the structure of the object with fields and types, and the
    DatabaseItem specifies how to retrieve them from a specific database.
    """

    def __init__(self, id_mapper: IdMapper, attributes: dict[str, Any]):
        """
        The `id_mapper` specifies how a unique backo `_id` can be built from the
        external database, and how the item can be queried later in the
        database.

        `attributes` is a dict mapping JSON fields to specification of database
        attributes. Here is a simple example for LDAP:
        ```
        {
            "name": Attribute("uid"),
            "description": Attribute("description")
        }
        ```
        With this example, the DatabaseItem will load() the JSON-like dict by
        loading values of `name` and `description` fields from the `uid` and
        `description` attributes of the LDAP response obtained from the result
        of the search performed using the search_request() parameters.

        :param id_mapper: Specifies how to map database entries to backo `_id`s.
        :param attributes: Specification of database attributes
        """
        self.id_mapper = id_mapper
        self.attributes = attributes

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

        :param _id: Backo ID of the item to search
        """

        # Builds request required by the `id_mapper` to perform the `base`
        # initialization of the `DatabaseItem` instance associated to an `_id`
        base_request = self.id_mapper.search_request(_id)

        #  Builds additional requests required to initialize all `attributes` of
        #  the `DatabaseItem`. Each attribute is allowed to either modify the
        #  `base_request`, build a new request or do nothing.
        attributes_requests = {}
        self._request_dict(
            base_request, attributes_requests, self.attributes, _id, _search_request
        )
        return base_request, attributes_requests

    def create_request(self, item_value):
        """Builds a set of search requests that will be able to load all the
        attributes required to load the item represented by `_id`.

        Responses obtained by the DatabaseEngine will then be passed to the
        created_id() method of the DatabaseItem.

        :param item_value: JSON-like dict with values of attributes of the new
        item
        """

        # Builds request required by the `id_mapper` to create the `item` with
        # value `item_value` and initialize its _id
        base_request = self.id_mapper.create_request(item_value)

        #  Builds additional requests required to create all `attributes` of the
        #  `DatabaseItem`. Each attribute is allowed to either modify the
        #  `base_request`, build a new request or do nothing.
        attributes_requests = {}
        self._request_dict_with_values(
            base_request,
            attributes_requests,
            self.attributes,
            item_value,
            _create_request,
        )
        return base_request, attributes_requests

    def delete_request(self, _id):
        """Builds a set of delete requests that will be able to delete all the
        attributes of the item represented by `_id` (and the item itself).

        :param _id: Backo ID of the item to delete
        """

        # Builds request required by the `id_mapper` to delete the item
        # corresponding to _id
        base_request = self.id_mapper.delete_request(_id)

        #  Builds additional requests required to delete all `attributes` of the
        #  `DatabaseItem`. Each attribute is allowed to either modify the
        #  `base_request`, build a new request or do nothing.
        attributes_requests = {}
        self._request_dict(
            base_request, attributes_requests, self.attributes, _id, _delete_request
        )
        return base_request, attributes_requests

    def update_request(self, _id, item_value):
        """Builds a set of update requests that will be able to update the
        attributes of the item represented by `_id` with values from
        `item_value`.

        :param _id: Backo ID of the item to update
        :param item_value: JSON-like dict with values of attributes of the new
        item
        """

        # Builds request required by the `id_mapper` to create the `item` with
        # value `item_value` and initialize its _id
        base_request = self.id_mapper.update_request(_id, item_value)

        #  Builds additional requests required to create all `attributes` of the
        #  `DatabaseItem`. Each attribute is allowed to either modify the
        #  `base_request`, build a new request or do nothing.
        attributes_requests = {}
        self._request_dict_with_id_and_values(
            base_request,
            attributes_requests,
            self.attributes,
            _id,
            item_value,
            _update_request,
        )
        return base_request, attributes_requests

    def _load_list(
        self, root_request_response, attributes_responses, item_list, attributes_list
    ):
        for i in range(len(attributes_list)):
            if isinstance(attributes_list[i], dict):
                item_value = {}
                self._load_dict(
                    root_request_response,
                    attributes_responses[i],
                    item_value,
                    attributes_list[i],
                )
                item_list.append(item_value)
            elif isinstance(attributes_list[i], list):
                item_value = []
                self._load_list(
                    root_request_response,
                    attributes_responses[i],
                    item_value,
                    attributes_list[i],
                )
                item_list.append(item_value)
            else:
                item_list.append(
                    attributes_list[i].load(
                        root_request_response, attributes_responses[i]
                    )
                )

    def _load_dict(
        self, root_request_response, attributes_responses, item_node, attributes_node
    ):
        for key, attribute in attributes_node.items():
            if isinstance(attribute, dict):
                item_node[key] = {}
                self._load_dict(
                    root_request_response,
                    attributes_responses[key],
                    item_node[key],
                    attribute,
                )
            elif isinstance(attribute, list):
                item_node[key] = []
                self._load_list(
                    root_request_response,
                    attributes_responses[key],
                    item_node[key],
                    attribute,
                )
            else:
                item_node[key] = attributes_node[key].load(
                    root_request_response, attributes_responses[key]
                )

    def load(self, root_request_response, attribute_responses):
        """Loads the item in a JSON-like dict from the database response.

        The response as been obtained by the DatabaseEngine from the request provided by
        search_request().

        The returned value is a JSON-like dict that can be used later to load a
        backo item using `item.load(loaded_json_dict)`.

        Notice the `_id` is not yet included in the result, as it only includes
        values retrieved using the `attributes` specification.
        """
        item = self.id_mapper.load(root_request_response)
        # TODO: attributes is not necessarily a dict
        self._load_dict(
            root_request_response, attribute_responses, item, self.attributes
        )
        return item

    def created_id(self, base_create_response):
        return self.id_mapper.id(base_create_response)
