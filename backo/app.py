"""
The App module
"""
# pylint: disable=logging-fstring-interpolation
from .generic import GenericDB
from .transaction import Transaction
from .log import log_system

log = log_system.get_or_create_logger("app")


class App:  # pylint: disable=too-many-instance-attributes
    """
    The main object, the aplication itself
    """

    def __init__(self, name):
        """
        initialize the app with a name
        """
        self.name = name
        self.collections = {}
        self.transaction_id_reference = 1
        self.transactions = {}

    def add_collection(self, name: str, coll: GenericDB):
        """
        Add a collection into the app
        """
        self.collections[name] = coll
        coll.set_app(self, name)
        setattr(self, name, coll)

    def new(self, name: str):
        """
        Return an new Object collection
        """
        return self.collections[name].copy()

    def start_transaction(self):
        """
        Chose an Id and start the transaction structure
        """
        self.transaction_id_reference = self.transaction_id_reference + 1
        my_id = self.transaction_id_reference
        self.transactions[my_id] = []
        return my_id

    def stop_transaction(self, transaction_id):
        """
        Close the transaction structure
        """
        del self.transactions[transaction_id]

    def record_transaction(self, transaction_id, collection, operation, _id, obj):
        """
        Append an object to the transaction
        """
        if not transaction_id:
            return
        self.transactions[transaction_id].append(
            Transaction(collection, operation, _id, obj)
        )

    def rollback_transaction(self, transaction_id):
        """
        An error occure, rollback objects
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
