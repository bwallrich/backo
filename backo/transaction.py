"""
The transaction module
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code, logging-fstring-interpolation

from enum import Enum, auto
from .log import log_system

log = log_system.get_or_create_logger("transaction")


class OperatorType(Enum):
    """
    Specifics status for this obj
    """

    CREATE = auto()
    DELETE = auto()
    UPDATE = auto()

    def __repr__(self):
        return self.name


class Transaction:  # pylint: disable=too-few-public-methods
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
        collection = app.collections.get(self.collection_name)

        # delete the created obj
        if self.operation == OperatorType.CREATE:
            log.debug(f"Rollback CREATION {self._id} -> delete {self._id}")
            collection.db_handler.delete_by_id(self._id)
            return

        # re-save the deleted obj
        if self.operation == OperatorType.DELETE:
            log.debug(f"Rollback DELETE {self._id} -> re-populate it")
            collection.db_handler.save(self._id, self.obj)
            return

        # re-save the updated obj
        if self.operation == OperatorType.UPDATE:
            log.debug(f"Rollback UPDATE {self._id} -> re-populate it")
            collection.db_handler.save(self._id, self.obj)
            return
