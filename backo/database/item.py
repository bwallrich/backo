from abc import ABC, abstractmethod
from .request import DatabaseSearchRequest
from typing import Any


class IdMapper(ABC):
    @abstractmethod
    def id(self, response) -> str:
        pass

    @abstractmethod
    def search_request(self, _id) -> DatabaseSearchRequest:
        pass

class BaseItem(ABC):
    @abstractmethod
    def base_item(self, base_response) -> dict:
        pass

class Empty(BaseItem):
    def base_item(self, _base_response):
        return {}

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

    def __init__(self, id_mapper: IdMapper, attributes: dict[str, Any], base = Empty()):
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
        self.base = base
        self.attributes = attributes

    def _search_request_list(self, root_request, request_list, attributes_list):
        for attribute in attributes_list:
            if isinstance(attribute, list):
                requests = []
                self._search_request_list(root_request, requests, attribute)
                request_list.append(requests)
            elif isinstance(attribute, dict):
                requests = {}
                self._search_request_dict(root_request, requests, attribute)
                request_list.append(requests)
            else:
                request_list.append(attribute.search_request(root_request))

    def _search_request_dict(self, root_request, request_dict, attributes_dict):
        for key, attribute in attributes_dict.items():
            if isinstance(attribute, list):
                requests = []
                self._search_request_list(root_request, requests, attribute)
                request_dict[key] = requests
            elif isinstance(attribute, dict):
                requests = {}
                self._search_request_dict(root_request, requests, attribute)
                request_dict[key] = requests
            else:
                request_dict[key] = attribute.search_request(root_request)

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
        self._search_request_dict(base_request, attributes_requests, self.attributes)
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
        item = self.base.base_item(root_request_response)
        # TODO: attributes is not necessarily a dict
        self._load_dict(root_request_response, attribute_responses, item, self.attributes)
        return item
