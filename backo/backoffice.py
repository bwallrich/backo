"""
The Backoffice module
"""

# pylint: disable=logging-fstring-interpolation

import json
from flask import Flask

from .item import Item
from .request_decorators import error_to_http_handler
from .transaction import Transaction, OperatorType
from .collection import Collection
from .log import log_system, Log_level


log = log_system.get_or_create_logger("backoffice", Log_level.INFO)


class Backoffice:  # pylint: disable=too-many-instance-attributes
    """
    Backoffice is tha application itself.

    :param name: A name for the application
    :type name: str

    .. code-block:: python


       from backo import Backoffice

       # example
       my_app = Backoffice("customer_app")

    """

    def __init__(self, name: str):
        """Constructor for backoffice"""
        self.name = name
        self.collections = {}
        self.transaction_id_reference = 1
        self.transactions = {}

    def register_collection(self, coll: Collection) -> None:
        """Register a collection into this backoffice

        :param coll: The collection to add.
        :type coll: Collection

        See :py:class:`Collection`

        """
        self.collections[coll.name] = coll
        coll.backoffice = self
        setattr(self, coll.name, coll)

    def add_collection(self, coll: Collection) -> None:
        """See :func:`register_collection`"""
        return self.register_collection(coll)

    def start_transaction(self) -> int:
        """Chose an id for the transaction and start the transaction structure

        See :py:class:`Transaction`

        :meta private:

        """
        self.transaction_id_reference += 1
        my_id = self.transaction_id_reference
        self.transactions[my_id] = []
        return my_id

    def stop_transaction(self, transaction_id: int) -> None:
        """Close the transaction structure

        See :py:class:`Transaction`

        :meta private:

        """
        del self.transactions[transaction_id]

    def record_transaction(
        self,
        transaction_id: int,
        collection: Collection,
        operation: OperatorType,
        _id: str,
        obj: Item,
    ) -> None:
        """
        Append an object to the transaction

        See :py:class:`Transaction`

        :meta private:

        """
        if not transaction_id:
            return
        self.transactions[transaction_id].append(
            Transaction(collection, operation, _id, obj)
        )

    def rollback_transaction(self, transaction_id: int) -> None:
        """An error occure, rollback objects

        See :py:class:`Transaction`

        :meta private:

        """
        log.info(
            "Rollback transactions %d with %d actions",
            transaction_id,
            len(self.transactions[transaction_id]),
        )
        while self.transactions[transaction_id]:
            t = self.transactions[transaction_id].pop()
            t.rollback(self)

        del self.transactions[transaction_id]

    def add_routes(self, flask_app: Flask, prefix: str = "", jwt_auth=None) -> None:
        """Add all routes to flask application

        :param flask_app: The Flask object
        :type flask_app: Flask
        :param prefix: an optional prefix to the path
        :type prefix: str
        :param jwt_auth: The token function

        """

        my_path = f"/{prefix}/{self.name}/" if prefix else f"/{self.name}"
        log.debug("Adding routes under %s", my_path)

        for collection in self.collections.values():
            blue_print = collection.create_routes()

            # Adding the jwt authentication for each route
            if jwt_auth is not None:
                blue_print.before_request(jwt_auth)

            flask_app.register_blueprint(
                blue_print, url_prefix=f"{my_path}/coll/{collection.name}"
            )

        flask_app.add_url_rule(
            f"{my_path}/_meta",
            f"_meta_{self.name}",
            methods=["GET"],
        )
        flask_app.view_functions[f"_meta_{self.name}"] = self._meta_http

    def get_meta(self):
        """
        Get all meta information for all collections, view, actions

        :meta private:


        """
        d = {"name": self.name, "collections": []}
        for collection in self.collections.values():
            d["collections"].append(collection.get_meta())
        return d

    @error_to_http_handler
    def _meta_http(self):
        """GET meta information :func:`get_meta` via https"""
        log.debug(f"get meta information for {self.name}")
        return (json.dumps(self.get_meta()), 200)
