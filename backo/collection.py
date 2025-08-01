"""
The Collection module
"""

# pylint: disable=logging-fstring-interpolation
import json
import logging
import re
import sys

from flask import request, session

sys.path.insert(1, "../../stricto")
from stricto import StrictoEncoder, Rights


from .item import Item
from .action import Action
from .error import Error, ErrorType
from .log import log_system
from .request_decorators import (
    return_http_error,
)
from .api_toolbox import multidict_to_filter


log = log_system.get_or_create_logger("collection", logging.DEBUG)


class Collection:
    """
    The Collection refer to a "table"
    """

    def __init__(self, name, model: Item, db_handler, **kwargs):
        """
        available arguments
        """
        self.db_handler = db_handler
        self.name = name
        self.model = model.copy()
        self.model.__dict__["_collection"] = self
        self.model.set_db_handler(db_handler)

        # Set rights
        self._rights = Rights(read=True, create=True, delete=True, modify=True)
        for key, right in kwargs.items():
            a = re.findall(r"^can_(.*)$", key)
            if a:
                self._rights.add_or_modify_right(a[0], right)

        # For filtering
        self.refuse_filter = kwargs.pop("refuse_filter", None)

        # For actions (aka some element work with datas)
        self._actions = {}
        self.app = None

        # For views
        self._views = {}

    def set(self, datas: dict | list) -> Item | list:
        """
        Set an object or a list of object
        """
        if isinstance(datas, dict):
            o = self.new_item()
            o.set(datas)
            return o

        if isinstance(datas, list):
            l = []
            for d in datas:
                l.append(self.set(d))
        return l

    def define_view(self, name: str, list_of_selector: list) -> None:
        """
        add element into views
        """
        for selector in list_of_selector:
            f = self.model.select(selector)
            if f is None:
                continue
            if name not in f._views:
                f._views.append(name)

    def has_right(self, right_name: str, o: Item = None) -> bool:
        """
        Return the right for this collection
        """
        return self._rights.has_right(right_name, o)

    def new_item(self):
        """
        return an Item
        """
        return self.model.copy()

    def new(self):
        """
        return an Item
        """
        return self.new_item()

    def create(self, obj: dict, **kwargs):
        """
        Create and save an item into the DB

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references
        """

        if self._rights.has_right("create", None) is not True:
            raise Error(
                ErrorType.RIGHT,
                f"No rights to create in collection {self.name}.",
            )

        item = self.new_item()
        item.create(obj, **kwargs)
        return item

    def get_other_collection(self, name):
        """
        Return another collection (ised by Ref and RefsList)
        """
        if self.app is None:
            raise Error(
                ErrorType.COLLECTION_NOT_REGISTERED,
                f"collection {self.name} not registered into an app",
            )
        return self.app.collections.get(name)

    def register_action(self, name: str, action: Action):
        """
        add an action to this collection
        this action will be related to an object
        """
        self._actions[name] = action
        action.__dict__["app"] = self.app
        action.__dict__["name"] = name
        action.__dict__["collection"] = self

    def add_action(self, name: str, action: Action):
        """
        add an action to this collection
        this action will be related to an object
        """
        return self.register_action(name, action)

    def drop(self):
        """
        Drop all elements
        """
        self.db_handler.drop()

    def get_by_id(self, _id):
        """
        return an object by Id.
        """

        if self._rights.has_right("read", None) is not True:
            raise Error(
                ErrorType.RIGHT,
                f"No rights to create in collection {self.name}.",
            )

        obj = self.new_item()
        obj.load(_id)
        return obj

    def select(
        self,
        db_filter,
        match_filter=None,
        view=None,
        page_size=0,
        num_of_element_to_skip=0,
        db_sort_object={"_id": 1},
    ):
        """
        Do a selection

        db_filter : Is a filter related to the database system
        match_filter : A filter for matching the object, independant
                       from the db. See match() in stricto
        view : The view we want (See views in stricto)

        """

        if self._rights.has_right("read", None) is not True:
            raise Error(
                ErrorType.RIGHT,
                f"No rights to read the entire collection {self.name}.",
            )

        # Do the DB selection without pagination
        db_list = self.db_handler.select(db_filter, {}, 0, 0, db_sort_object)
        if not isinstance(db_list, list):
            raise Error(
                ErrorType.SELECT_ERROR,
                f"select {self.name} error",
            )
        result = {
            "result": [],
            "total": 0,
            "view": view,
            "skip": num_of_element_to_skip,
            "page_size": page_size,
        }

        # Get the restriction filter
        # rfilter = (
        #     self.refuse_filter() if callable(self.refuse_filter) else self.refuse_filter
        # )

        # Do the selection on the object
        index = 0
        log.debug(f"try match {match_filter} for {len(db_list)}")
        for obj in db_list:
            obj["_id"] = str(obj["_id"])
            o = self.new_item()
            o.set(obj)
            # Do the post match filtering

            # Ignore all elements matched by the refuse filter
            if self._rights.has_right("read", o) is not True:
                continue

            if o.match(match_filter) is True:
                if index >= num_of_element_to_skip:
                    if page_size == 0 or (
                        page_size > 0 and index < (num_of_element_to_skip + page_size)
                    ):
                        result["result"].append(o)
                index += 1
            else:
                log.debug(f"Not matchs {match_filter} for {o}")

        result["total"] = index
        return result

    def flask_add_routes(self, flask_app, prefix=""):
        """
        Add CRUD routes and add axtions routes
        """

        if self._rights.get_strict_right("read") is not False:
            # GET /<_id>
            flask_app.add_url_rule(
                f"{prefix}/{self.name}/<string:_id>",
                f"get_{self.name}",
                methods=["GET"],
            )
            flask_app.view_functions[f"get_{self.name}"] = self.http_get_by_id

            # GET / - The selection
            flask_app.add_url_rule(
                f"{prefix}/{self.name}", f"select_{self.name}", methods=["GET"]
            )
            flask_app.view_functions[f"select_{self.name}"] = self.filtering

            # POST / The creation
            flask_app.add_url_rule(
                f"{prefix}/{self.name}", f"create_{self.name}", methods=["POST"]
            )
            flask_app.view_functions[f"create_{self.name}"] = self.http_create

    def http_get_by_id(self, _id: str):
        """
        GET HTTP
        """
        query = request.args
        _view = query.get("_view", "client")

        log.debug(f"session {session.keys()}")

        obj = self.new_item()

        try:
            obj.load(_id)
        except Error as e:
            if e.error_code == ErrorType.NOTFOUND:
                return return_http_error(204, "No content")
            if e.error_code == ErrorType.UNAUTHORIZED:
                return return_http_error(401, "Unauthorized")

            log.debug(f"get by _id {_id} in {self.name} return error {e}")
            return return_http_error(500, f"Internal Server Error : {e}")

        log.debug(f"get by _id {_id} in {self.name} in view {_view}")
        return (json.dumps(obj.get_view(_view), cls=StrictoEncoder), 200)

    def filtering(self):
        """
        SELECT HTTP
        """
        query = request.args
        _page = int(query.get("_page", 10))
        _skip = int(query.get("_skip", 0))
        _view = query.get("_view", "client")

        match_filter = multidict_to_filter(query)

        log.debug(f"filtering {self.name} with filter={match_filter}")

        result = self.select(None, match_filter, _view, _page, _skip)
        log.debug(
            f"select in {self.name} {match_filter} {_view}/{_page} skip {_skip} -> {result}"
        )

        return (json.dumps(result, cls=StrictoEncoder), 200)

    def http_create(self, _id: str):
        """
        POST HTTP -> creation
        """
        query = request.args
        _view = query.get("_view", "client")

        log.debug(f"session {session.keys()}")

        obj = self.new_item()

        try:
            self.create(request.form)
        except Error as e:
            if e.error_code == ErrorType.RIGHT:
                return return_http_error(401, "Unauthorized")
            return return_http_error(500, f"Internal Server Error : {e}")

        log.debug(f"create {obj._id} in {self.name} in view {_view}")
        return (json.dumps(obj.get_view(_view), cls=StrictoEncoder), 200)
