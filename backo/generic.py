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

    def can_modify_creation_meta(self, value, o): # pylint: disable=unused-argument
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
        result._collection_name = self._collection_name
        result._status = self._status
        result.__dict__["_locked"] = True
        return result

    def new(self):
        """
        return a emty object of this collection
        """
        return copy.copy(self._empty)

    def load(self, _id: str):
        """
        Read in the database by Id and fill the Data
        """
        if self._status != StatusType.UNSET:
            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot load an non-unset object in {self._collection_name}",
            )
        obj = self.db.get_by_id(_id)
        self.set(obj)
        self.__dict__["_status"] = StatusType.SAVED
        self.trigg("loaded", id(self))

        print(f"Load {int(datetime.timestamp(datetime.now()))}", self)

    def save(self, transaction_id=None):
        """
        save the object.
        """
        if self._status == StatusType.UNSET:
            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot save an unset object in {self._collection_name}",
            )

        self.trigg("save", id(self))
        timestamp = int(datetime.timestamp(datetime.now()))
        self._meta.mtime = timestamp
        self._meta.modified_by.user_id = current_user.user_id.copy()
        self._meta.modified_by.login = current_user.login.copy()

        print(f"Save {int(datetime.timestamp(datetime.now()))}", self)

        self.db.save(self._id.get_value(), self.get_value())
        self.__dict__["_status"] = StatusType.SAVED

        # Record into the app translation
        self.app.record_transaction(
            transaction_id,
            self._collection_name,
            OperatorType.UPDATE,
            self._id.get_value(),
            self.get_value(),
        )

        self.trigg("saved", id(self))

    def delete(self, transaction_id=None):
        """
        delete the object in the database
        """
        if self._status == StatusType.UNSET:
            raise Error(
                ErrorType.UNSET_SAVE,
                f"Cannot delete an unset object in {self._collection_name}",
            )

        # Send delete event before deletion to do  some stufs
        self.trigg("deletion", id(self))
        self.db.delete_by_id(self._id.get_value())
        self.__dict__["_status"] = StatusType.UNSET

        # Record into the app translation
        self.app.record_transaction(
            transaction_id,
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

    def create(self, obj: dict, transaction_id=None):
        """
        Create and save an object into the DB
        """
        # Set the object

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
            transaction_id,
            self._collection_name,
            OperatorType.CREATE,
            self._id.get_value(),
            None,
        )

        self.trigg("created", id(self))
