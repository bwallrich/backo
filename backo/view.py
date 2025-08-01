"""
The Collection module
"""

# pylint: disable=logging-fstring-interpolation
import logging

# import sys
# sys.path.insert(1, "../../stricto")
# from stricto import Dict, Int, String, StrictoEncoder

# from .item import Item
# from .action import Action
from .error import Error, ErrorType
from .log import log_system

log = log_system.get_or_create_logger("collection", logging.DEBUG)


class View:
    """
    The View refer to a "table"
    """

    def __init__(
        self,
        name,
        collection,
        selectors: list,
    ):
        """
        available arguments
        """
        self.name = name
        self._collection = collection
        self.selectors = selectors

        for sel in selectors:
            obj = collection.model.select(sel)
            print(f"obj {sel} {type(obj)}= {obj}")
            if obj is None:
                raise Error(
                    ErrorType.SELECTOR_NOT_FOUND,
                    f"collection {collection.name} doesn't have selector {sel}",
                )
            if self.name not in obj._views:
                obj._views.append(self.name)

    def get_by_id(self, _id):
        """
        return an object by Id.
        """
        obj = self._collection.new_item()
        obj.load(_id)
        return obj.get_view(f"+{self.name}")

    def wip(self):
        """
        not yet
        """
