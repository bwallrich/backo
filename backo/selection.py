"""
The Collection module
"""

# pylint: disable=logging-fstring-interpolation
import logging

import sys

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Permissions

# from .item import Item
# from .action import Action
from .collection_addon import CollectionAddon
from .log import log_system
from .error import Error, ErrorType


log = log_system.get_or_create_logger("select", logging.DEBUG)


class Selection(CollectionAddon):
    """
    The View refer to a "table"
    """

    def __init__(self, selectors: list[str] = None, **kwargs):
        """
        available arguments
        """
        self._selectors = selectors
        self._filter = kwargs.pop("filter", None)
        self._db_filter = kwargs.pop("db_filter", None)

        if "can_read" not in kwargs:
            kwargs["can_read"] = True

        CollectionAddon.__init__(self)
        self._permissions = Permissions(**kwargs)

    def can_read(self) -> bool:
        """
        return True if permission to read
        """
        return self.is_allowed_to("read")

    def select(
        self,
        match_filter=None,
        page_size=0,
        num_of_element_to_skip=0,
        db_sort_object={"_id": 1},
    ):
        """
        Do the selection
        """
        if self.collection is None:
            raise Error(
                ErrorType.DEVELOPPER,
                "This selection is not registered.",
            )

        if self.can_read() is False:
            raise Error(
                ErrorType.UNAUTHORIZED,
                f"Execute {self.name} selection is forbidden.",
            )

        # Do the DB selection without pagination
        db_list = self.collection.db_handler.select(
            self._db_filter, {}, 0, 0, db_sort_object
        )
        if not isinstance(db_list, list):
            raise Error(
                ErrorType.SELECT_ERROR,
                f"select {self.name} database error",
            )

        output = {
            "result": [],
            "total": 0,
            "_skip": num_of_element_to_skip,
            "_page": page_size,
        }

        # Do the selection on the object
        index = 0
        log.debug(f"try match {match_filter} for {len(db_list)}")
        for obj in db_list:
            obj["_id"] = str(obj["_id"])
            o = self.collection.new_item()

            o.set(obj)
            o.enable_permissions()
            o.set_status_saved()
            # Do the post match filtering

            # Ignore all elements matched by the refuse filter
            if self.collection._permissions.is_allowed_to("read", o) is not True:
                continue

            if o.match(match_filter) is True:
                if index >= num_of_element_to_skip:
                    if page_size == 0 or (
                        page_size > 0 and index < (num_of_element_to_skip + page_size)
                    ):
                        output["result"].append(o.multi_select(self._selectors))
                index += 1
            else:
                log.debug(f"No match {match_filter} for {o}")

        output["total"] = index
        return output
