"""
The Collection module
"""

# pylint: disable=logging-fstring-interpolation, too-many-public-methods
import json
import sys
from typing import Self, Callable

from flask import request, Blueprint

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import (
    Permissions,
    StrictoEncoder,
    FreeDict,
    Dict,
    String,
    STypeError,
    SAttributeError,
    SSyntaxError,
    SConstraintError,
    SError,
    SRightError,
    Kparse,
    validation_parameters,
)


from .item import Item
from .action import Action
from .selection import Selection
from .error import PathNotFoundError
from .log import log_system, LogLevel
from .request_decorators import error_to_http_handler, check_json
from .api_toolbox import multidict_to_filter, append_path_to_filter
from .patch import Patch

log = log_system.get_or_create_logger("collection", LogLevel.INFO)

check_model_request = Dict(
    {"path": String(required=True, default="$"), "item": FreeDict(default={})}
)
meta_model_request = FreeDict(default={})

KPARSE_MODEL = {
    "can_read|read": {"type": bool | Callable, "default": True},
    "can_modify|modify|write|can_write|can_update|update": {
        "type": bool | Callable,
        "default": True,
    },
    "can_delete|delete": {"type": bool | Callable, "default": True},
    "can_create|create": {"type": bool | Callable, "default": True},
    "refuse_filter": Callable,
}


class Collection:
    """The Collection refer to a "table"

    A collection is the main object in backo. It contains
        - an :py:class:`Item` = the description of the object structure
        - an :py:class:`DBConnector` = the database connector to say how and where to save the object
        - some :py:class:`Selection` = some preset *select* for this collection
        - some :py:class:`Action` = a list of actions to do on this collection

    A collection mus by registered into a :py:class:`Backoffice` with :func:`Backoffice.register_collection`

    :param name: The collection name
    :param model: The description of the structure (an Item)
    :type model: Item
    :param db_handler: The database handler
    :type db_handler: DBConnector

    :param ``**kwargs``:
        - *refuse_filter=* ``func`` --
          not used yet
        - *can_read=* ``[func]|bool`` --
          a function to say if the :py:class:`CurrentUser` can read this collection
        - *can_create=* ``[func]|bool`` --
          a function to say if the :py:class:`CurrentUser` can create an :py:class:`Item` in this collection
        - *can_delete=* ``[func]|bool`` --
          a function to say if the :py:class:`CurrentUser` can delete an :py:class:`Item` in this collection
        - *can_modify=* ``[func]|bool`` --
          a function to say if the :py:class:`CurrentUser` can modify an :py:class:`Item` in this collection



    .. code-block:: python

        from backo import Item, Collection, Backoffice, , DBMongoConnector

        # example
        book_item = Item({
            "title": String(),
            "subtitle": String(),
            "author": Ref(collection="authors", field="$.books", required=True),
        })


        database_for_books = DBMongoConnector( connection_string="mongodb://localhost:27017/bookcase" )
        books = Collection( "books", book_item, database_for_books )

        my_bookstore = Backoffice("bookstore")
        my_bookstore.register_collection(books)
        # ...



    """

    @validation_parameters
    def __init__(self, name: str, model: Item, db_handler, **kwargs):
        """Constructor"""
        self.db_handler = db_handler
        self.name = name
        self.model = model.copy()
        self.model.__dict__["_collection"] = self
        self.model.set_db_handler(db_handler)

        options = Kparse(kwargs, KPARSE_MODEL, strict=True)

        # Set permissions
        self._permissions = Permissions(
            read=True, create=True, delete=True, modify=True
        )
        self._permissions.add_or_modify_permission("read", options.get("can_read"))
        self._permissions.add_or_modify_permission("create", options.get("can_create"))
        self._permissions.add_or_modify_permission("modify", options.get("can_modify"))
        self._permissions.add_or_modify_permission("delete", options.get("can_delete"))

        self._permissions.enable()

        # For filtering
        self.refuse_filter = options.get("refuse_filter")

        # For actions (aka some element work with datas)
        self._actions = {}
        self.backoffice = None

        # For views
        self._views = {}

        self._selections = {}

        # Adding the "_all" selection
        can_read = self._permissions.get("read", True)
        self.register_selection("_all", Selection(None, can_read=can_read))

    def get_meta(self) -> dict:
        """Return the meta data for this collection and actions

        :meta private:

        """
        d = {"name": self.name, "item": self.model.get_schema()}
        return d

    def set(self, datas: dict | list) -> Item | list:
        """Set an object or a list of object

        :meta private:


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

    def define_view(self, name: str, list_of_selector: list[str]) -> None:
        """
        add element into views


        :meta private:

        """
        for selector in list_of_selector:
            f = self.model.select(selector)
            if f is None:
                continue
            if name not in f._views:
                f._views.append(name)

    def is_allowed_to(self, right_name: str, o: Item = None) -> bool:
        """
        Return the right for this collection


        :meta private:

        """
        return self._permissions.is_allowed_to(right_name, o)

    def new_item(self) -> Item:
        """Return an empty :py:class:`Item`

        :return: an empty Item
        :rtype: Item
        """
        return self.model.copy()

    def new(self):
        """See :func:`new_item`


        :meta private:

        """
        return self.new_item()

    def create(self, obj: dict, **kwargs) -> Item:
        """Create and save an item into the DB

        :param obj: The json object struture to create
        :type obj: dict

        :return: an empty Item
        :rtype: Item

        :param ``**kwargs``:
            - *transaction_id=* ``int`` -- the current transaction_id (in case of rollback)
            - *m_path=* ``[str]`` -- the modification path, to to avoid loop with references

        """

        item = self.new_item()
        item.create(obj, **kwargs)
        item.enable_permissions()
        return item

    def get_other_collection(self, name) -> Self:
        """Return another collection (used by :py:class:`Ref` and :py:class:`RefsList`)

        :param name: the name of the collection you want
        :return: the collection
        :rtype: Self
        """
        if self.backoffice is None:
            raise SSyntaxError(
                "Collection {0} not registered into an backoffice", self.name
            )

        return self.backoffice.collections.get(name)

    @validation_parameters
    def register_action(self, name: str, action: Action):
        """Register an action to this collection

        :param name: The name of the action
        :type name: str
        :param action: the :py:class:`Action` to register
        :type action: :py:class:`Action`

        """
        self._actions[name] = action
        action.__dict__["backoffice"] = self.backoffice
        action.__dict__["name"] = name
        action.__dict__["collection"] = self

    def add_action(self, name: str, action: Action):
        """See :func:`register_action`"""
        return self.register_action(name, action)

    def register_selection(self, selection_name: str, selection: Selection) -> None:
        """Register a selction to this collection

        :param name: The name of the selection
        :type name: str
        :param action: the :py:class:`Selection` to register
        :type action: :py:class:`Selection`

        """
        self._selections[selection_name] = selection
        selection.backoffice = self.backoffice
        selection.name = selection_name
        selection.collection = self

    def drop(self):
        """
        Drop all elements for this collection

        :meta private:


        """
        self.db_handler.drop()

    def get_by_id(self, _id: str) -> Item:
        """Return an object by Id.


        :param _id: the _id of the Item you want
        :type _id: str
        :return: The item
        :rtype: Item

        """

        if self._permissions.is_allowed_to("read", None) is not True:
            raise SRightError("No permission to create in collection {0}", self.name)

        obj = self.new_item()
        obj.load(_id)
        obj.enable_permissions()
        return obj

    def select(self, filter_for_selection: dict) -> list[Item]:
        """Do a selection directly with a filter

        :param filter_for_selection: a filter
        :type filter_for_selection: dict
        :return: a list of Items
        :rtype: list[Item]
        """
        result = self._selections["_all"].select(filter_for_selection, 0, 0)
        return result["result"]

    def select_one(self, filter_for_selection: dict) -> Item:
        """select one item (if only one)

        :param filter_for_selection: a filter
        :type filter_for_selection: dict
        :return: The one Item matching the filter
        :rtype: Item
        """
        result = self._selections["_all"].select(filter_for_selection, 0, 0)
        if len(result["result"]) != 1:
            return None
        return result["result"][0]

    def create_routes(self) -> Blueprint:
        """Add CRUD/_meta/_check routes

        :meta private:

        """
        collection_blueprint = Blueprint(f"{self.name}", __name__)

        # read datas
        if self._permissions.is_strictly_allowed_to("read") is not False:
            # GET / - The selection
            log.info(f"Add route GET {self.name}/")
            collection_blueprint.add_url_rule("", "select", methods=["GET"])
            collection_blueprint.view_functions[f"{self.name}.select"] = self.filtering

        # POST / Create data
        if self._permissions.is_strictly_allowed_to("create") is not False:
            log.info(f"Add route POST {self.name}/")
            collection_blueprint.add_url_rule("", "create", methods=["POST"])
            collection_blueprint.view_functions[f"{self.name}.create"] = (
                self.http_create
            )

        # CHECK / Check values
        if self._permissions.is_strictly_allowed_to("modify") is not False:
            log.info(f"Add route POST {self.name}/_check")
            collection_blueprint.add_url_rule(
                "/_check",
                "check",
                methods=["POST"],
            )
            collection_blueprint.view_functions[f"{self.name}.check"] = self.http_check

        # META /> Check values
        if self._permissions.is_strictly_allowed_to("modify") is not False:
            log.info(f"Add route GET {self.name}/_meta")
            collection_blueprint.add_url_rule(
                "/_meta",
                "meta",
                methods=["POST"],
            )
            collection_blueprint.view_functions[f"{self.name}.meta"] = self.http_meta

        if self._permissions.is_strictly_allowed_to("read") is not False:
            # GET /<_id>
            log.info(f"Add route GET {self.name}/<string:_id>")

            collection_blueprint.add_url_rule(
                "/<string:_id>",
                "get",
                methods=["GET"],
            )
            collection_blueprint.view_functions[f"{self.name}.get"] = (
                self.http_get_by_id
            )

        # PUT /<_id> Modify Data
        if self._permissions.is_strictly_allowed_to("modify") is not False:
            log.info(f"Add route PUT {self.name}/<string:_id>")
            collection_blueprint.add_url_rule(
                "/<string:_id>",
                "put",
                methods=["PUT"],
            )
            collection_blueprint.view_functions[f"{self.name}.put"] = self.http_modify

        # PATCH /<_id> Modify Data
        if self._permissions.is_strictly_allowed_to("modify") is not False:
            log.info(f"Add route PATCH {self.name}/<string:_id>")
            collection_blueprint.add_url_rule(
                "/<string:_id>",
                "patch_one",
                methods=["PATCH"],
            )
            collection_blueprint.view_functions[f"{self.name}.patch_one"] = (
                self.http_patch_one
            )

        # DELETE /<_id> Delete Data
        if self._permissions.is_strictly_allowed_to("delete") is not False:
            log.info(f"Add route DELETE {self.name}/<string:_id>")
            collection_blueprint.add_url_rule(
                "/<string:_id>",
                "delete",
                methods=["DELETE"],
            )
            collection_blueprint.view_functions[f"{self.name}.delete"] = (
                self.http_delete
            )

        # Actions
        if self._permissions.is_strictly_allowed_to("read") is not False:
            log.info(
                "Add route POST action /_actions/<string:_action_name>/<string:_id>"
            )
            collection_blueprint.add_url_rule(
                "/_actions/<string:_action_name>/<string:_id>",
                "go",
                methods=["POST"],
            )
            collection_blueprint.view_functions[f"{self.name}.go"] = self.action_go

        # Selections
        if self._permissions.is_strictly_allowed_to("read") is not False:
            log.info("Add route GET selections /_selections/<string:_selection_name>")
            collection_blueprint.add_url_rule(
                "/_selections/<string:_selection_name>",
                "do_selection",
                methods=["GET"],
            )
            collection_blueprint.view_functions[f"{self.name}.do_selection"] = (
                self.do_selection
            )
            log.info("Add route POST selections /_selections/<string:_selection_name>")
            collection_blueprint.add_url_rule(
                "/_selections/<string:_selection_name>",
                "do_post_selection",
                methods=["POST"],
            )
            collection_blueprint.view_functions[f"{self.name}.do_post_selection"] = (
                self.do_post_selection
            )

        return collection_blueprint

    @check_json
    @error_to_http_handler
    def action_go(self, _action_name: str, _id: str):
        """_summary_

        :param _id: The _id
        :type _id: str
        :raises Error: _description_
        :return: _description_
        :rtype: _type_
        """

        if _action_name not in self._actions:
            raise SSyntaxError(
                'collection "{0}" has no action "{1}"', self.name, _action_name
            )

        # Set the action
        action = self._actions.get(_action_name)
        action.set(request.json)

        # set the object
        obj = self.new_item()
        obj.load(_id)

        log.debug(f"lauch action {_action_name} for {_id}")
        action.go(obj)

        return ("action done", 200)

    @error_to_http_handler
    def http_get_by_id(self, _id: str):
        """
        GET HTTP

        :meta private:

        """

        log.debug(f"http_get_by_id _id {_id}")

        query = request.args
        _view = query.get("_view", "client")

        obj = self.new_item()
        obj.load(_id)

        log.debug(f"get by _id {_id} in {self.name} in view {_view}")
        return (json.dumps(obj.get_view(_view), cls=StrictoEncoder), 200)

    @error_to_http_handler
    def filtering(self):
        """
        SELECT HTTP

        :meta private:

        """
        log.debug(f"filtering request.args {request.args}")
        query = request.args
        _page = int(query.get("_page", 10))
        _skip = int(query.get("_skip", 0))

        match_filter = multidict_to_filter(query)

        log.debug(f"filtering {self.name}/_all with filter={match_filter}")

        result = self._selections["_all"].select(match_filter, _page, _skip)

        log.debug(
            f"select in {self.name}/_all {match_filter}/{_page} skip {_skip} -> {result}"
        )

        return (json.dumps(result, cls=StrictoEncoder), 200)

    @error_to_http_handler
    def do_selection(self, _selection_name: str):
        """_summary_

        :param _selection_name: The name of the selection
        :type _selection_name: str
        :raises Error: _description_
        :return: _description_
        :rtype: _type_
        """

        if _selection_name not in self._selections:
            raise SSyntaxError(
                "Collection {0} has no selection {0}", self.name, _selection_name
            )

        query = request.args
        _page = int(query.get("_page", 10))
        _skip = int(query.get("_skip", 0))

        match_filter = multidict_to_filter(query)
        result = self._selections[_selection_name].select(match_filter, _page, _skip)

        log.debug(
            f"select in {self.name}/{_selection_name} {match_filter}/{_page} skip {_skip} -> {result}"
        )

        return (json.dumps(result, cls=StrictoEncoder), 200)

    @check_json
    @error_to_http_handler
    def do_post_selection(self, _selection_name: str):
        """Do a selection with filter given in post

        :param _selection_name: The name of the selection
        :type _selection_name: str
        :raises Error: _description_
        :return: _description_
        :rtype: _type_
        """

        if _selection_name not in self._selections:
            raise SSyntaxError(
                "Collection {0} has no selection {0}", self.name, _selection_name
            )

        query = request.args
        _page = int(query.get("_page", 10))
        _skip = int(query.get("_skip", 0))

        match_filter = {}
        for key, v in request.json.items():
            append_path_to_filter(match_filter, key, v)
        result = self._selections[_selection_name].select(match_filter, _page, _skip)

        log.debug(
            f"select in {self.name}/{_selection_name} {match_filter}/{_page} skip {_skip} -> {result}"
        )

        return (json.dumps(result, cls=StrictoEncoder), 200)

    @check_json
    @error_to_http_handler
    def http_create(self):
        """
        POST HTTP -> creation

        :meta private:

        """

        log.debug(f"http_create request {request.json}")

        query = request.args
        _view = query.get("_view", "client")

        log.debug(f"post {type(request.json)} {request.json}")
        obj = self.create(request.json)

        log.debug(f"create {obj._id} in {self.name} in view {_view}")
        return (json.dumps(obj.get_view(_view), cls=StrictoEncoder), 200)

    @check_json
    @error_to_http_handler
    def http_modify(self, _id: str):
        """
        PUT HTTP -> modification of an object

        :meta private:

        """

        log.debug(f"http_modify request {request.json}")

        query = request.args
        _view = query.get("_view", "client")

        obj = self.new_item()
        obj.load(_id)
        obj.set(request.json)
        obj.save()

        return (json.dumps(obj.get_view(_view), cls=StrictoEncoder), 200)

    @error_to_http_handler
    def http_delete(self, _id: str):
        """
        DELETE HTTP -> deletion

        :meta private:

        """
        log.debug(f"http_delete _id {_id}")

        obj = self.new_item()
        obj.load(_id)
        obj.delete()

        return ("deleted", 200)

    @check_json
    @error_to_http_handler
    def http_check(self):
        """
        POST HTTP -> check value if a field

        :meta private:

        """

        log.debug(f"http_check request {request.json}")

        c = check_model_request.copy()
        c.set(request.json)

        # Create a partial object with values given in request.item
        obj = self.new_item()
        obj.set_value_without_checks(c.item.get_value())
        obj.enable_permissions()
        sub_object = obj.select(c.path)
        if sub_object is None:
            raise PathNotFoundError(
                'Path "{0}" not found in collection "{1}"', c.path, self.name
            )

        try:
            sub_object.check(sub_object.get_value())
            return (json.dumps({"error": None}), 200)
        except (
            STypeError,
            SSyntaxError,
            SConstraintError,
            SAttributeError,
            SRightError,
            SError,
        ) as e:
            return (json.dumps({"error": e.to_string()}), 200)

    @check_json
    @error_to_http_handler
    def http_meta(self):
        """
        POST HTTP -> get a meta structure for this context

        :meta private:

        """

        log.debug(f"http_meta request {request.json}")

        c = meta_model_request.copy()
        c.set(request.json)

        # Create a partial object with values given in request.item
        obj = self.new_item()
        obj.set_value_without_checks(c.get_value())
        obj.enable_permissions()

        return (json.dumps(obj.get_current_meta()), 200)

    @check_json
    @error_to_http_handler
    def http_patch_one(self, _id: str):
        """
        PATCH HTTP -> patch of an object

        :meta private:

        """
        query = request.args
        _view = query.get("_view", "client")

        patch_list = request.json if isinstance(request.json, list) else [request.json]

        obj = self.new_item()
        obj.load(_id)

        # apply patches
        for p in patch_list:
            patch = Patch()
            patch.set(p)
            obj.patch(patch.op, patch.path, patch.value)

        obj.save()

        return (json.dumps(obj.get_view(_view), cls=StrictoEncoder), 200)
