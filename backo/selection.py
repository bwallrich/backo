"""
The Collection module
"""

# pylint: disable=logging-fstring-interpolation
import logging
import copy
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
    The Selection refer to a select on a "table"

    A collection must by registered into a :py:class:`Collection` with :func:`Collection.register_selection`

    :param selectors: The list of paths we went to see in the selection
    :type selectors: list[str]

    :param ``**kwargs``:
        - *filter=* ``dict|tuple`` --
          the filter whe want. See stricto for details
        - *db_filter=* ``dict`` --
          The filter to pass to the :py:class:`DBConnector`



    .. code-block:: python

        from backo import Item, Collection, Selection

        # example
        book_item = Item({
            "title": String(),
            "subtitle": String(),
            "author": Ref(collection="authors", field="$.books", required=True),
        })

        database_for_books = DBMongoConnector( connection_string="mongodb://localhost:27017/bookcase" )
        books = Collection( "books", book_item, database_for_books )

        fb = Selection( [ "$.title", "$.subtitle" ], filter={ "$.author.nationality.a2" : "FR" } )
        books.register_selection("french_book", fb )

        nfb = Selection( [ "$.title", "$.subtitle" ], filter={ "$.author.nationality.a2" : ( "$ne", "FR" ) } )
        books.register_selection("non_french_book", nfb )

        # ...
    """

    def __init__(self, selectors: list[str] = None, **kwargs):
        """
        Selection constructor

        :param ``**kwargs``:
        - *filter=* ``dict|tuple`` --
          the filter whe want. See stricto for details
        - *db_filter=* ``dict`` --
          The filter to pass to the :py:class:`DBConnector`

        """

        self._selectors = selectors
        if self._selectors is not None and "$._id" not in self._selectors:
            self._selectors.insert(0, "$._id")

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

    def _merge_and_filter(self, f1: dict, f2: dict) -> dict:
        """Merge 2 object in a sens of a filter


        :param f1: filter1
        :type f1: dict
        :param f2: filter2
        :type f2: dict
        :return: a new dict with is the merge of f1 and f2
        :rtype: dict
        """
        f = copy.copy(f1) if f1 is not None else {}

        if not isinstance(f2, dict):
            return f

        for key, value in f2.items():
            if key not in f:
                f[key] = copy.copy(value)
                continue
            if isinstance(f[key], dict):
                if isinstance(value, dict):
                    f[key] = self._merge_and_filter(f[key], value)
                    continue
            f[key] = ("$and", [f[key], value])

        return f

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

        # build the filter with filter given and self_filter
        # --------------------------------------------------
        filter_object = self._merge_and_filter(self._filter, match_filter)

        # Do the selection on the object
        index = 0
        log.debug(f"try match {filter_object} for {len(db_list)}")
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

            if o.match(filter_object) is True:
                if index >= num_of_element_to_skip:
                    if page_size == 0 or (
                        page_size > 0 and index < (num_of_element_to_skip + page_size)
                    ):
                        output["result"].append(o.multi_select(self._selectors))
                index += 1
            else:
                log.debug(f"No match {filter_object} for {o}")

        output["total"] = index
        return output
