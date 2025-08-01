"""
Module providing the Item() Class
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys
import copy
import hashlib
import json

from .error import Error, ErrorType
from .db_connector import DBConnector
from .current_user import current_user
from .transaction import OperatorType
from .log import log_system
from .meta_data_handler import StandardMetaDataHandler
from .status import StatusType


log = log_system.get_or_create_logger("Item")

sys.path.insert(1, "../../stricto")
from stricto import Dict, String


class Item(Dict):  # pylint: disable=too-many-instance-attributes
    """
    A generic type for a DB
    """

    def __init__(self, schema: dict, **kwargs):
        """
        available arguments
        """
        self.db_handler = None
        self.meta_data_handler = kwargs.pop(
            "meta_data_handler", StandardMetaDataHandler()
        )
        self._loaded_object = None
        self._status = StatusType.UNSET
        self._collection = None
        Dict.__init__(self, schema, **kwargs)

        # adding _id to the model
        self.add_to_model("_id", String())

        # Setting meta schema
        if self.meta_data_handler:
            self.meta_data_handler.append_schema(self)

    def set_db_handler(self, db_connector: DBConnector) -> None:
        """
        Set or modify the Database Handler
        """
        self.__dict__["db_handler"] = db_connector

    def compute_hash_schema(self, schema: dict):
        """
        Compute the Hash of the schema
        (to add in meta data to help, on load, to see if the db structure change)
        """
        dhash = hashlib.md5()
        dhash.update(json.dumps(schema, sort_keys=True).encode())
        return dhash.hexdigest()

    def __copy__(self):
        """
        Make a copy of thos object
        """
        result = Dict.__copy__(self)
        result.__dict__["_locked"] = False
        result.db_handler = self.db_handler
        result._collection = self._collection
        result._status = self._status
        result._loaded_object = self._loaded_object
        result.__dict__["_locked"] = True
        return result

    def load(self, _id: str, **kwargs) -> None:
        """
        Read in the database by Id and fill the Data

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references

        """
        if self._status != StatusType.UNSET:
            log.error("Cannot load an non-unset object in %r", self._collection.name)

            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot load an non-unset object in {self._collection.name}",
            )

        _id_to_load = _id.get_value() if isinstance(_id, String) else str(_id)

        obj = self.db_handler.get_by_id(_id_to_load)
        self.set(obj)
        self.__dict__["_status"] = StatusType.SAVED
        self.__dict__["_loaded_object"] = copy.copy(self)

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        self.trigg("loaded", id(self), **kwargs)

        # print(f"Load {int(datetime.timestamp(datetime.now()))}", self)

    def reload(self, **kwargs) -> None:
        """
        Reload from DB the object

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references

        """
        if self._status != StatusType.SAVED:
            log.error("Cannot reload an unset object in %r", self._collection.name)
            raise Error(
                ErrorType.RELOAD_UNSED,
                f"Cannot reload an unset object in {self._collection.name}",
            )
        obj = self.db_handler.get_by_id(self._id.get_value())
        # set as UNSET to be able to modify meta datas.
        self.__dict__["_status"] = StatusType.UNSET
        self.set(obj)
        self.__dict__["_status"] = StatusType.SAVED
        self.__dict__["_loaded_object"] = copy.copy(self)

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        self.trigg("loaded", id(self), **kwargs)

    def save(self, **kwargs) -> None:
        """
        save the object.

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references

        """
        if self._status == StatusType.UNSET:
            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot save an unset object in {self._collection.name}",
            )

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.debug(
            "try to save %r/%r with transaction_id=%r",
            self._collection.name,
            self._id,
            kwargs.get("transaction_id"),
        )

        # Check if right to create
        if self._collection.has_right("modify", self) is not True:
            raise Error(
                ErrorType.RIGHT,
                f"No rights to modify element in collection {self.self._collection}.",
            )

        if self.meta_data_handler:
            self.meta_data_handler.set_on_save(self)

        # Load the previous value in the DB (for transactions and comparison of values )
        if self.__dict__["_loaded_object"] is None:
            a = copy.copy(self)
            a.__dict__["_status"] = StatusType.UNSET
            a.load(self._id.get_value())
            self.__dict__["_loaded_object"] = a

        kwargs["old_object"] = self.__dict__["_loaded_object"]
        self.trigg("before_save", id(self), **kwargs)

        # print(f"Save {int(datetime.timestamp(datetime.now()))}", self)
        dict_to_save = self.get_view("save").get_value()

        self.db_handler.save(self._id.get_value(), dict_to_save)

        log.info(
            "%r/%r modified by %r/%r",
            self._collection.name,
            self._id,
            current_user.user_id,
            current_user.login,
        )

        self.__dict__["_status"] = StatusType.SAVED

        # Record into the app translation
        self._collection.app.record_transaction(
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

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references

        """
        if self._status == StatusType.UNSET:
            log.error("Cannot delete an unset object in %r", self._collection.name)
            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot delete an unset object in {self._collection.name}",
            )

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.debug(
            "try to delete %r/%r with transaction_id=%r",
            self._collection.name,
            self._id,
            kwargs.get("transaction_id"),
        )

        # Check if right to create
        if self._collection.has_right("delete", self) is not True:
            raise Error(
                ErrorType.RIGHT,
                f"No rights to delete in collection {self.self._collection}.",
            )

        # Send delete event before deletion to do  some stufs
        self.trigg("deletion", id(self), **kwargs)
        self.db_handler.delete_by_id(self._id.get_value())

        log.info(
            "%r/%r deleted by %r/%r",
            self._collection.name,
            self._id,
            current_user.user_id,
            current_user.login,
        )

        self.__dict__["_status"] = StatusType.UNSET

        # Record into the app translation
        self._collection.app.record_transaction(
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
        """
        return self.db_handler.generate_id(self)

    def create(self, obj: dict, **kwargs):
        """
        Create and save an object into the DB

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references
        """
        # Set the object
        log.debug(
            "try to create new object in %r with transaction_id=%r, obj=%r",
            self._collection.name,
            kwargs.get("transaction_id"),
            obj,
        )

        # Check if right to create
        if self._collection.has_right("create") is not True:
            raise Error(
                ErrorType.RIGHT,
                f"No rights to create in collection {self.self._collection}.",
            )

        self.set(obj)
        # Set _meta
        if self.meta_data_handler:
            self.meta_data_handler.set_on_create(self)

        # Set the _id
        self._id = self.create_uniq_id()

        # create
        dict_to_save = self.get_value()
        self._id = self.db_handler.create(dict_to_save)

        self.__dict__["_status"] = StatusType.SAVED

        # Record into the app translation
        self._collection.app.record_transaction(
            kwargs.get("transaction_id"),
            self._collection.name,
            OperatorType.CREATE,
            self._id.get_value(),
            None,
        )

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.info(
            "%r/%r created by %r/%r",
            self._collection.name,
            self._id,
            current_user.user_id,
            current_user.login,
        )
        self.trigg("created", id(self), **kwargs)
