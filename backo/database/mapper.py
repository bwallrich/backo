"""Provides the specification of the ItemMapper interface."""

class ItemMapper:
    """ Base requests handling to support each database operations.

    Each ItemMapper implementation is specific to a database type, but several
    ItemMappers might be defined for each database, depending on how data is
    structured in the database.

    For example, in the case of an LDAP database, the `MapByDN` item mapper
    might identify items using their DN, while the MapByAttribute(search_base,
    "id") might identify items using the "id" attribute of each entry within the
    search_base.

    How to map database specific ids to item _ids is actually a core feature of
    the ItemMapper, as ID mapping is the minimum requirement of each base
    request.

    For example, it defines how the `_id` provided to the search_request must be
    used to build the base request that will be used by all attributes to manage
    the item associated to `_id`.

    For example, a `MapSqlKey("table", "id")` SQL item mapper will likely
    generate a search base request that is equivalent to `SELECT * FROM "table"
    WHERE "id" == _id`. Each SQL attribute in the model might then specialize
    selected fields in the request.

    Any DatabaseAttribute should be compatible with any ItemMapper as long as
    they use the same database request types.
    """

    def created_id(self, create_response) -> str:
        """Retrieve the id of the created item from the response of the base
        create request.

        The id is a string that can be later provided to search_request(),
        delete_request() or update_request() methods to work on the item.

        :param create_response: Response of the base create request. Its type
        is implementation dependent.
        """
        raise NotImplementedError("This ItemMapper does not support item creation")

    def search_request(self, _id):
        """Builds a request that can be used as a base request to search the
        item associated to _id.

        :param _id: ID of the item to search
        :return: A search request. Its type is implementation dependent.
        """
        raise NotImplementedError("This ItemMapper does not support item search")

    def create_request(self, item_value):
        """Builds a request that can be used as a base request to create a new
        item with the specified value.

        :param item_value: Initial values of attributes for the new item
        :return: A create request. Its type is implementation dependent.
        """
        raise NotImplementedError("This ItemMapper does not support item creation")

    def delete_request(self, _id):
        """Builds a request that can be used as a base request to delete a new
        item with the specified value.

        :param _id: ID of the item to delete
        :return: A delete request. Its type is implementation dependent.
        """
        raise NotImplementedError("This ItemMapper does not support item deletion")

    def update_request(self, _id, item_value):
        """Builds a request that can be used as a base request to update the
        item associated to _id with the specified value.

        :param _id: ID of the item to update
        :param item_value: New values of attributes for the item
        :return: A delete request. Its type is implementation dependent.
        """
        raise NotImplementedError("This ItemMapper does not support item update")

    def load(self, _base_response):
        """Loads the base JSON-like dict representation of an item from the
        response of the base request.

        Database attributes will then increment this representation as required.
        The item can also be completely loaded from the base_response.
        """
