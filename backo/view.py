"""
The Collection module
"""

# pylint: disable=logging-fstring-interpolation

# import sys
# used for developpement
# sys.path.insert(1, "../../stricto")

# from stricto import Dict, Int, String, StrictoEncoder

# from .item import Item
# from .action import Action
from .error import PathNotFoundError
from .log import log_system, LogLevel

log = log_system.get_or_create_logger("collection", LogLevel.INFO)


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
            if obj is None:
                raise PathNotFoundError('Path "{0}" not found in collection "{1}"', sel, collection.name)
            
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
