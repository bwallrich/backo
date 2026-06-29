"""Provides the specification of the DatabaseAttribute interface."""


class DatabaseAttribute:
    """Interface that should be implemented by attributes available for each
    database.

    DatabaseAttributes are the building blocks of DatabaseItem models. For
    example, a DatabaseItem might be defined as follows:
    ```python
    database_item = DatabaseItem(
            item_mapper=...,
            model={
                "name": SomeAttribute(),
                "data": [SqlAttribute(column="value", table="data"), OtherAttribute("custom")],
                "nested": {
                    "value": SomeAttribute(parameter="foo")
                }
            }
        )
    ```
    The purpose of the attribute is to build any request required to support
    each operation on itself, and only itself. This as two main advantages:
    - when you implement an attribute for a given database, you only need to
      focus on the atomic operations that will be performed on the field, as the
      global model is managed by the DatabaseEngine.
    - attributes are modular building blocks that can be used to specify complex
      model structures.
    """

    def __init__(self, connection=None):
        """Initializes the DatabaseAttribute.

        It is very likely that you will need to define a custom constructor to
        provide parameters to the user that are specific to both the attribute
        itself and the type of database. But parameters should be specific to the
        attribute, as connection parameters are handled by the DatabaseConnection
        that will execute requests.

        For example, if you want to define an Attribute that fetch the value of
        a column in an SQL table, the Attribute will require `column` and
        `table` parameters but not the URL of the SQL database, that will be
        provided to the DatabaseConnection.

        For each operation, the attribute is allowed to either modify the
        `base_request`, build a new request or more, or do nothing.

        Modifying the base_request allows to fine tune a single request to avoid
        executing a new request for each attribute. For example, add a column to
        the SELECT statement of the base_request.

        On the other hand, building new requests might be required if the value
        of the attribute cannot be computed from a single base request. For
        example, in a model representing an LDAP user, an extra request to a
        group entry might be required to check if the current user is in the
        group.

        Finally, nothing might be done for an operation if it is ensured that
        the execution of the base request will lead to the desired result. For
        example, since an SQL DELETE deletes the all line associated to the
        item, the value of each column is implicitly and necessarily deleted
        when the base DELETE is executed.

        When new requests are built, each operation can either return a single
        request, or a complex dict/list structure with several requests. For
        example,
        ```python
        [request_1, {"data": [request_2, request_3]}]
        ```
        is a valid return value. All requests will be executed by the
        DatabaseEngine and returned to the item if required, e.g. in the load()
        method.

        The nature of the `_id` passed to some operation depends on the database
        and the ItemMapper currently in use.

        :param connection: Custom DatabaseConnection that will be used to
        execute requests produced by this item. Otherwise, the connection
        provided to set_default_connection by the DatabaseEngine will be used.
        """
        self.connection = connection
        self.attribute_path = None

    def set_default_connection(self, connection):
        """Sets the default connection used to execute requests produced by this
        item.

        If a custom connection was already assigned to this item, this method
        has no effect.
        """
        if self.connection is None:
            self.connection = connection

    def set_attribute_path(self, attribute_path):
        """Sets the path of the attribute within the model.

        The attribute_path is a list of keys or list indexes that defined where
        the attribute is located with the model of the DatabaseItem.

        For example, considering the following model:
        ```python
        database_item = DatabaseItem(
            item_mapper,
            model={
                "name": attribute_0,
                "nested": {
                    "data": [
                        [attribute_1, attribute_2],
                        attribute_3,
                        {"nested_data": attribute_4},
                    ],
                    "time": attribute_5,
                },
            },
        )
        ```
        The path of each attribute will be set as follows:
        - `attribute_0`: `["name"]`,
        - `attribute_1`: `["nested", "data", 0, 0]`,
        - `attribute_2`: `["nested", "data", 0, 1]`,
        - `attribute_3`: `["nested", "data", 1]`,
        - `attribute_4`: `["nested", "data", 2, "nested_data"]`,
        - `attribute_5`: `["nested", "time"]`,

        This might be useful to define some default values of attributes. For
        example, in the case of a JSON database, creating a `JsonAttribute()`
        without parameter might mean to look for the attribute at the same path
        in the JSON file as the path of the attribute in the model. This allows
        to write
        ```
        {
            "very": {
                "nested": [
                    ..., {"attribute": JsonAttribute()}, ...
                    ]
                }
        }
        ```
        instead of
        ```
        {
            "very": {
                "nested": [
                    ..., {"attribute": JsonAttribute(["very", "nested", 1, "attribute"])}, ...
                    ]
                }
        }
        ```
        what is much more convenient for the final user.

        More complex database structures might also be deduced from the
        attribute_path if required.
        """
        self.attribute_path = attribute_path

    def search_request(self, base_request, _id):
        """Builds requests required to fetch the value of the attribute.

        :param base_request: Base request that was build by the ItemMapper to search
        for the item associated to `_id`.
        :param _id: ID of the item to search.
        """

    def create_request(self, base_request, value):
        """Builds requests required to create the value of the attribute.

        :param base_request: Base request that was build by the ItemMapper to create
        the base item.
        :param value: Value that should be assigned to the attribute itself
        """

    def update_request(self, base_request, _id, value):
        """Builds requests required to update the value of the attribute.

        :param base_request: Base request that was build by the ItemMapper to update
        the item associated to `_id`.
        :param _id: ID of the item to update.
        :param value: Value that should be assigned to the attribute itself
        """

    def delete_request(self, base_request, _id):
        """Builds requests required to delete the attribute.

        :param base_request: Base request that was build by the ItemMapper to
        delete the item associated to `_id`.
        :param _id: ID of the item to delete.
        """

    def select_request(self, base_request, _id):
        pass

    def load(self, base_response, attribute_response):
        """Returns the value of the attribute computed from specified database
        responses.

        Once all requests associated to the model was executed by the
        DatabaseEngine, the attribute received only responses to the requests it
        is responsible for, depending on what is returned by the search_request:
        - if it was nothing, attribute_response is None
        - if it was a single request, attribute_response is what was returned by
          the DatabaseConnection to execute this search request
        - if it was dict/list structure, the attribute_response is a structure
          with the same shape where requests have been replaced by responses.

        The base_response is the same for all attributes of the model.

        :base_response: Response to the base_request that was specified in the
        search_request call
        :attribute_response: Responses to the requests returned by the
        search_request call
        """
