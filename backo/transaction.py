"""
The transaction module
"""
from enum import Enum, auto

class OperatorType(Enum):
    """
    Specifics status for this obj
    """

    CREATE = auto()
    DELETE = auto()
    UPDATE = auto()

    def __repr__(self):
        return self.name

class Transaction: # pylint: disable=too-few-public-methods

    """
    The Transaction Object
    """

    def __init__(self, collection_name, operation, _id, obj):
        """
        Create the transaction
        """
        self.collection_name = collection_name
        self.operation = operation
        self._id = _id
        self.obj = obj

    def rollback(self, app):
        """
        Do a rollback on this action
        """
        c = app.new(self.collection_name)

        # delete the created obj
        if self.operation == OperatorType.CREATE:
            c.db.delete_by_id(self._id)
            return

        # re-save the deleted obj
        if self.operation == OperatorType.DELETE:
            c.db.save(self._id, self.obj)
            return

        # re-save the updated obj
        if self.operation == OperatorType.UPDATE:
            c.db.save(self._id, self.obj)
            return
