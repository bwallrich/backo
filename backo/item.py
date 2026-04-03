"""
Module providing the Item() Class
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys
import copy

from .error import BackoError
from .db_connector import DBConnector
from .transaction import OperatorType
from .log import log_system
from .meta_data_handler import StandardMetaDataHandler
from .status import StatusType


log = log_system.get_or_create_logger("Item")

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Dict, String, SRightError


class Item(Dict):  # pylint: disable=too-many-instance-attributes
    """The description of the object of a collection

    :param schema: its schema (see `Dict <https://stricto.readthedocs.io/en/latest/api_reference.html#stricto.Dict>`)
    :type schema: dict
    :param ``**kwargs``: see https://stricto.readthedocs.io/en/latest/api_reference.html#stricto.Dict

    .. code-block:: python

        from backo import Item, Collection, Backoffice, DBMongoConnector

        # example
        book = Item({
            "title": String(),
            "subtitle": String(),
            "author": Ref(coll="authors", field="$.books", required=True),
            "pages": Int()
        })

        database_for_books = DBMongoConnector( connection_string="mongodb://localhost:27017/bookcase" )
        books = Collection( book, database_for_books )

        bookstore = Backoffice("bookstore")
        bookstore.register_collection(books)
        # ...

    """

    def __init__(self, schema: dict, **kwargs):
        """
        Constructor
        """
        self.db_handler = None
        self.meta_data_handler = kwargs.pop(
            "meta_data_handler", StandardMetaDataHandler()
        )
        self._loaded_object = None
        self._status = StatusType.UNSET
        self._collection = None

        Dict.__init__(self, schema, **kwargs)

        # Append then change event to the item
        if "change" not in self._events:
            self._events["change"] = []
        self._events["change"].append(self.on_change)

        # adding _id to the model
        self.add_to_model("_id", String())

        # Setting meta schema
        if self.meta_data_handler:
            self.meta_data_handler.append_schema(self)

    def set_db_handler(self, db_connector: DBConnector) -> None:
        """
        Set or modify the Database Handler

        :meta private:

        """
        self.__dict__["db_handler"] = db_connector

    def on_change(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        some value has change into this Item, chang its status to UNSAVED
        if it was previously SAVED
        This is trigged by the "change" event

        :meta private:

        """
        if me._status == StatusType.SAVED:
            me.set_status_unsaved()

    def __copy__(self):
        """
        Make a copy of this object
        """
        result = Dict.__copy__(self)
        result.__dict__["_locked"] = False
        result.db_handler = self.db_handler
        result._collection = self._collection
        result._status = self._status
        result._loaded_object = self._loaded_object
        result.__dict__["_locked"] = True
        return result

    def set_status_unsaved(self):
        """
        Set as StatusType.UNSAVED

        :meta private:

        """
        self.__dict__["_status"] = StatusType.UNSAVED

    def set_status_saved(self):
        """
        Set as StatusType.SAVED

        :meta private:

        """
        self.__dict__["_status"] = StatusType.SAVED

    def set_status_unset(self):
        """
        Set as StatusType.UNSET

        :meta private:

        """
        self.__dict__["_status"] = StatusType.UNSET

    def load(self, _id: str, **kwargs) -> None:
        """Read in the database by Id and fill the Data


        :param _id: The _id to load.
        :type _id: str


        :param ``**kwargs``:
            - *transaction_id=* ``int`` -- the current transaction_id (in case of rollback)
            - *m_path=* ``[str]`` -- the modification path, to to avoid loop with references

        """
        if self._status != StatusType.UNSET:
            raise BackoError('Cannot load an non-unset object in {0}', self._collection.name)

        _id_to_load = _id.get_value() if isinstance(_id, String) else str(_id)

        obj = self.db_handler.get_by_id(_id_to_load)
        self.disable_permissions()
        self.set(obj)
        self.enable_permissions()
        self.set_status_saved()
        self.__dict__["_loaded_object"] = copy.copy(self)

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        self.trigg("loaded", id(self), **kwargs)

        # print(f"Load {int(datetime.timestamp(datetime.now()))}", self)

    def reload(self, **kwargs) -> None:
        """Reload from DB the object (in case of changement)

        :param ``**kwargs``:
            - *transaction_id=* ``int`` -- the current transaction_id (in case of rollback)
            - *m_path=* ``[str]`` -- the modification path, to to avoid loop with references

        """
        if self._status != StatusType.SAVED:
            raise BackoError('Cannot reload an unset object in {0}', self._collection.name)
        
        obj = self.db_handler.get_by_id(self._id.get_value())
        # set as UNSET to be able to modify meta datas.
        self.set_status_unset()

        self.disable_permissions()
        self.set(obj)
        self.enable_permissions()

        self.set_status_saved()
        self.__dict__["_loaded_object"] = copy.copy(self)

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        self.trigg("loaded", id(self), **kwargs)

    def save(self, **kwargs) -> None:
        """
        save the object in the database.

        :param ``**kwargs``:
            - *transaction_id=* ``int`` -- the current transaction_id (in case of rollback)
            - *m_path=* ``[str]`` -- the modification path, to to avoid loop with references


        """
        if self._status == StatusType.UNSET:
            raise BackoError('Cannot save an unset object in {0}', self._collection.name)

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.debug(
            "try to save %r/%r with transaction_id=%r",
            self._collection.name,
            self._id,
            kwargs.get("transaction_id"),
        )

        # Check if right to create
        if self._collection.is_allowed_to("modify", self) is not True:
            raise SRightError("No permission to modify element in collection {0}", self._collection.name)

        if self.meta_data_handler:
            self.meta_data_handler.update(self)

        # Load the previous value in the DB (for transactions and comparison of values )
        if self.__dict__["_loaded_object"] is None:
            a = copy.copy(self)
            a.set_status_unset()
            a.load(self._id.get_value())
            self.__dict__["_loaded_object"] = a

        kwargs["old_object"] = self.__dict__["_loaded_object"]
        self.trigg("before_save", id(self), **kwargs)

        # print(f"Save {int(datetime.timestamp(datetime.now()))}", self)
        dict_to_save = self.get_view("save").get_value()

        self.db_handler.save(self._id.get_value(), dict_to_save)

        log.info("%r/%r modified", self._collection.name, self._id)

        self.set_status_saved()

        # Record into the backoffice translation
        self._collection.backoffice.record_transaction(
            kwargs.get("transaction_id"),
            self._collection.name,
            OperatorType.UPDATE,
            self._id.get_value(),
            self.__dict__["_loaded_object"].get_value(),
        )

        self.trigg("saved", id(self), **kwargs)

    def delete(self, **kwargs) -> None:
        """
        delete the object in the database

        :param ``**kwargs``:
            - *transaction_id=* ``int`` -- the current transaction_id (in case of rollback)
            - *m_path=* ``[str]`` -- the modification path, to to avoid loop with references

        """
        if self._status == StatusType.UNSET:
            raise BackoError('Cannot delete an unset object in {0}', self._collection.name)

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.debug(
            "try to delete %r/%r with transaction_id=%r",
            self._collection.name,
            self._id,
            kwargs.get("transaction_id"),
        )

        # Check if right to create
        if self._collection.is_allowed_to("delete", self) is not True:
            raise SRightError("No permission to delete in collection {0}", self._collection.name)

        # Send delete event before deletion to do  some stufs
        self.trigg("before_delete", id(self), **kwargs)
        self.db_handler.delete_by_id(self._id.get_value())

        log.info(
            "%r/%r deleted",
            self._collection.name,
            self._id,
        )

        self.set_status_unset()

        # Record into the backoffice translation
        self._collection.backoffice.record_transaction(
            kwargs.get("transaction_id"),
            self._collection.name,
            OperatorType.DELETE,
            self._id.get_value(),
            self.get_value(),
        )

    def create_uniq_id(self) -> str:
        """
        Create an _id before creation.
        Depends on the db_connector used. some of them needs _ids

        is probably overwritten


        :meta private:


        """
        return self.db_handler.generate_id(self)

    def create(self, obj: dict, **kwargs):
        """
        Create and save an object into the DB


        :param obj: The json object struture to create
        :type obj: dict

        :param ``**kwargs``:
            - *transaction_id=* ``int`` -- the current transaction_id (in case of rollback)
            - *m_path=* ``[str]`` -- the modification path, to to avoid loop with references


        """
        # Set the object
        log.debug(
            "try to create new object in %r with transaction_id=%r, obj=%r",
            self._collection.name,
            kwargs.get("transaction_id"),
            obj,
        )

        # Check if right to create
        if self._collection.is_allowed_to("create") is not True:
            raise SRightError("No permission to create in collection {0}", self._collection.name)
        
        self.set(obj)

        # Lock permissions
        self.enable_permissions()

        # Set _meta
        if self.meta_data_handler:
            self.meta_data_handler.update(self)

        # Set the _id
        self._id = self.create_uniq_id()

        # create
        dict_to_save = self.get_value()
        self._id = self.db_handler.create(dict_to_save)

        self.set_status_saved()

        # Record into the backoffice translation
        self._collection.backoffice.record_transaction(
            kwargs.get("transaction_id"),
            self._collection.name,
            OperatorType.CREATE,
            self._id.get_value(),
            None,
        )

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.info(
            "%r/%r created",
            self._collection.name,
            self._id,
        )
        self.trigg("created", id(self), **kwargs)
