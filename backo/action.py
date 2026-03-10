"""
Module providing the action
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init


import sys
from typing import Callable

sys.path.insert(1, "../../stricto")
from stricto import Dict

from .log import log_system
from .error import Error, ErrorType
from .item import Item

log = log_system.get_or_create_logger("action")


class Action(Dict):  # pylint: disable=too-many-instance-attributes
    """The action to do on a collection

    :param schema: The data schema needed for this action (see `Dict <https://stricto.readthedocs.io/en/latest/api_reference.html#stricto.Dict>`)
    :type schema: dict
    :param on_trig: the function to trig on the action
    :type on_trig: Callable
    :param ``**kwargs``: see https://stricto.readthedocs.io/en/latest/api_reference.html#stricto.Dict
        - *can_see=* ``[func]|bool`` -- a function to say if this action exists
        - *can_execute=* ``[func]|bool`` -- a function to say if the :py:class:`CurrentUser` can execute this action.


    .. code-block:: python

        from backo import Item, Collection, Backoffice, Action, Ref, DBMongoConnector

        # example
        book_item = Item({
            "title": String(),
            "subtitle": String(),
            "author": Ref(coll="authors", field="$.books", required=True),
            "score": Float( default=5.0 )
            "number_of_voter" : Int(default=0)
        })

        def do_vote(action, o):
            o.score = (o.score * o.number_of_voter + action.score) / ( o.number_of_voter + 1 )
            o.number_of_voter += 1


        vote_action = Action( {
            "score" : Float( max=10.0, min=0.0 )
        }, do_vote)

        database_for_books = DBMongoConnector( connection_string="mongodb://localhost:27017/bookcase" )
        books = Collection( "books", book_item, database_for_books )
        books.register_action( "vote", vote_action )

        my_bookstore = Backoffice("bookstore")
        my_bookstore.register_collection(books)
        # ...

    """

    def __init__(self, schema: dict, on_trig: Callable, **kwargs):
        """
                :param schema: The data schema needed for this action (see `Dict <https://stricto.readthedocs.io/en/latest/api_reference.html#stricto.Dict>`)
        :type schema: dict
        :param on_trig: the function to trig on the action
        :type on_trig: Callable
        :param ``**kwargs``: see https://stricto.readthedocs.io/en/latest/api_reference.html#stricto.Dict
            - *can_see=* ``[func]|bool`` -- a function to say if this action exists
            - *can_execute=* ``[func]|bool`` -- a function to say if the :py:class:`CurrentUser` can execute this action.


        """
        self.backoffice = None
        self.name = None
        self.collection = None
        self.on_trig = on_trig

        # Add default right
        if "can_execute" not in kwargs:
            kwargs["can_execute"] = True
        if "can_see" not in kwargs:
            kwargs["can_see"] = True
        kwargs["can_read"] = True
        kwargs["can_modify"] = True
        if "exists" not in kwargs:
            kwargs["exists"] = True

        Dict.__init__(self, schema, **kwargs)

    def check_params(self, param_name, o: Item) -> bool:
        """
        Check if can execute the action

        :meta private:


        """
        p = self._params.get(param_name, False)
        if not callable(p):
            return bool(p)
        return bool(p(self.backoffice, self.collection, self, o))

    def can_see(self, o: Item) -> bool:
        """Check if this action exists for running

        :param o: The current item
        :type o: Item
        :return: True if the action exists
        :rtype: bool


        :meta private:


        """
        return self._permissions.is_allowed_to("see", o)

    def can_execute(self, o: Item) -> bool:
        """
        Check if can execute the action

        object can be a Dict, a array of Dict, or None, depends ont the target for this action

        :param o: The current item
        :type o: Item
        :return: True if the action can be executed
        :rtype: bool

        :meta private:


        """
        return self._permissions.is_allowed_to("execute", o)

    def go(self, o: Item) -> None:
        """
                Launch the action
        elf,
                object is the object (if exists)

                :meta private:

        """

        if not self.can_see(o):
            log.error("Try to launch non available action %r", self.name)
            raise Error(
                ErrorType.ACTION_NOT_AVAILABLE,
                f"action {self.name} not available",
            )

        if not self.can_execute(o):
            log.error("Try to execute forbidden action %r", self.name)
            raise Error(
                ErrorType.ACTION_FORBIDDEN,
                f"action {self.name} forbidden",
            )

        log.debug("Execute action %r", self.name)
        return self.on_trig(self, o)
