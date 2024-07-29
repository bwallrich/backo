"""
Module providing the GenericDB() Class
"""
# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys
import copy
from datetime import datetime
from enum import Enum, auto
from .error import Error, ErrorType
from .db_connector import DBConnector
from .current_user import current_user
from .transaction import OperatorType
from .log import log_system

log = log_system.get_or_create_logger("GenericDB")

sys.path.insert(1, "../../stricto")
from stricto import Dict, Int, String


class StatusType(Enum):
    """
    Specifics status for this object
    """

    UNSET = auto()
    SAVED = auto()
    UNSAVED = auto()

    def __repr__(self):
        return self.name


class GenericDB(Dict):  # pylint: disable=too-many-instance-attributes
    """
    A generic type for a DB
    """

    def __init__(self, schema: dict, db_connector: DBConnector, **kwargs):
        """
        available arguments
        """
        self.db = db_connector
        self.app = None
        self._empty = None
        self._loaded_object = None
        self._status = StatusType.UNSET
        self._collection_name = ""
        Dict.__init__(self, schema, **kwargs)

        # Adding metadata
        self.add_to_model(
            "_meta",
            Dict(
                {
                    "ctime": Int(can_modify=self.can_modify_creation_meta),
                    "mtime": Int(),
                    "created_by": Dict(
                        {"user_id": String(), "login": String()},
                        can_modify=self.can_modify_creation_meta,
                    ),
                    "modified_by": Dict({"user_id": String(), "login": String()}),
                }
            ),
        )

        # adding _id to the model
        self.add_to_model("_id", String())
        self.__dict__["_locked"] = False
        self._empty = copy.copy(self)
        self.__dict__["_locked"] = True
        self._empty.__dict__["_locked"] = True

    def can_modify_creation_meta(self, value, o):  # pylint: disable=unused-argument
        """
        ctime and created_by cannot be modified by user
        """
        if o._status == StatusType.UNSET:
            return True
        return False

    def set_app(self, app, collection_name):
        """
        set the _app value to all Ref
        (_app is use to check of data exists for references)
        """
        self.__dict__["app"] = app
        self.__dict__["_collection_name"] = collection_name
        self._empty.__dict__["app"] = app
        self._empty.__dict__["_collection_name"] = collection_name

    def __copy__(self):
        result = Dict.__copy__(self)
        result.__dict__["_locked"] = False
        result.db = self.db
        result.app = self.app
        result._empty = self._empty
        result._collection_name = self._collection_name
        result._status = self._status
        result._loaded_object = self._loaded_object
        result.__dict__["_locked"] = True
        return result

    def new(self):
        """
        return a emty object of this collection
        """
        return copy.copy(self._empty)

    def load(self, _id: str, **kwargs):
        """
        Read in the database by Id and fill the Data

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references

        """
        if self._status != StatusType.UNSET:
            log.error("Cannot load an non-unset object in %r", self._collection_name)

            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot load an non-unset object in {self._collection_name}",
            )
        obj = self.db.get_by_id(_id)
        self.set(obj)
        self.__dict__["_status"] = StatusType.SAVED
        self.__dict__["_loaded_object"] = copy.copy(self)

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        self.trigg("loaded", id(self), **kwargs)

        # print(f"Load {int(datetime.timestamp(datetime.now()))}", self)

    def reload(self, **kwargs):
        """
        Reload from DB the object

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references

        """
        if self._status != StatusType.SAVED:
            log.error("Cannot reload an unset object in %r", self._collection_name)
            raise Error(
                ErrorType.RELOAD_UNSED,
                f"Cannot reload an unset object in {self._collection_name}",
            )
        obj = self.db.get_by_id(self._id.get_value())
        # set as UNSET to be able to modify meta datas.
        self.__dict__["_status"] = StatusType.UNSET
        self.set(obj)
        self.__dict__["_status"] = StatusType.SAVED
        self.__dict__["_loaded_object"] = copy.copy(self)

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        self.trigg("loaded", id(self), **kwargs)

    def save(self, **kwargs):
        """
        save the object.

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references

        """
        if self._status == StatusType.UNSET:
            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot save an unset object in {self._collection_name}",
            )

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.debug(
            "try to save %r/%r with transaction_id=%r",
            self._collection_name,
            self._id,
            kwargs.get("transaction_id"),
        )

        timestamp = int(datetime.timestamp(datetime.now()))
        self._meta.mtime = timestamp
        self._meta.modified_by.user_id = current_user.user_id.copy()
        self._meta.modified_by.login = current_user.login.copy()

        # Load the previous value in the DB (for transactions and comparison of values )
        if self.__dict__["_loaded_object"] is None:
            a = copy.copy(self)
            a.__dict__["_status"] = StatusType.UNSET
            a.load(self._id.get_value())
            self.__dict__["_loaded_object"] = a

        kwargs["old_object"] = self.__dict__["_loaded_object"]
        self.trigg("before_save", id(self), **kwargs)

        # print(f"Save {int(datetime.timestamp(datetime.now()))}", self)

        self.db.save(self._id.get_value(), self.get_value())

        log.info(
            "%r/%r modified by %r/%r",
            self._collection_name,
            self._id,
            current_user.user_id,
            current_user.login,
        )

        self.__dict__["_status"] = StatusType.SAVED

        # Record into the app translation
        self.app.record_transaction(
            kwargs.get("transaction_id"),
            self._collection_name,
            OperatorType.UPDATE,
            self._id.get_value(),
            self.__dict__["_loaded_object"].get_value(),
        )

        self.trigg("saved", id(self), **kwargs)

    def delete(self, **kwargs):
        """
        delete the object in the database

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references

        """
        if self._status == StatusType.UNSET:
            log.error("Cannot delete an unset object in %r", self._collection_name)
            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot delete an unset object in {self._collection_name}",
            )

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.debug(
            "try to delete %r/%r with transaction_id=%r",
            self._collection_name,
            self._id,
            kwargs.get("transaction_id"),
        )

        # Send delete event before deletion to do  some stufs
        self.trigg("deletion", id(self), **kwargs)
        self.db.delete_by_id(self._id.get_value())

        log.info(
            "%r/%r deleted by %r/%r",
            self._collection_name,
            self._id,
            current_user.user_id,
            current_user.login,
        )

        self.__dict__["_status"] = StatusType.UNSET

        # Record into the app translation
        self.app.record_transaction(
            kwargs.get("transaction_id"),
            self._collection_name,
            OperatorType.DELETE,
            self._id.get_value(),
            self.get_value(),
        )

    def create_uniq_id(self):
        """
        Create an _id before creation.
        Depends on the db_connector used. some of them needs _ids

        is probably overwritten
        """
        return self.db.generate_id(self)

    def create(self, obj: dict, **kwargs):
        """
        Create and save an object into the DB

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references
        """
        # Set the object
        log.debug(
            "try to create new object in %r with transaction_id=%r, obj=%r",
            self._collection_name,
            kwargs.get("transaction_id"),
            obj,
        )

        self.set(obj)
        # Set _meta
        self._meta.created_by.user_id = current_user.user_id.copy()
        self._meta.created_by.login = current_user.login.copy()
        self._meta.modified_by.user_id = current_user.user_id.copy()
        self._meta.modified_by.login = current_user.login.copy()

        timestamp = int(datetime.timestamp(datetime.now()))
        self._meta.ctime = timestamp
        self._meta.mtime = timestamp

        # Set the _id
        self._id = self.create_uniq_id()

        # create
        self._id = self.db.create(self.get_value())

        self.__dict__["_status"] = StatusType.SAVED

        # Record into the app translation
        self.app.record_transaction(
            kwargs.get("transaction_id"),
            self._collection_name,
            OperatorType.CREATE,
            self._id.get_value(),
            None,
        )

        if kwargs.get("m_path") is None:
            kwargs["m_path"] = []

        log.info(
            "%r/%r created by %r/%r",
            self._collection_name,
            self._id,
            current_user.user_id,
            current_user.login,
        )
        self.trigg("created", id(self), **kwargs)
