"""
Module providing the mongo DB like
"""
# pylint: disable=logging-fstring-interpolation
import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson.objectid import ObjectId
from pymongo.uri_parser import parse_uri

from .db_connector import DBConnector
from .error import Error, ErrorType
from .log import log_system

log = log_system.get_or_create_logger("mongo")
log.setLevel(logging.DEBUG)


class DBMongoConnector(DBConnector):  # pylint: disable=too-many-instance-attributes
    """
    A generic type for a DB
    """

    def __init__(self, **kwargs):
        """
        available arguments
        """
        self._connection_string = kwargs.pop(
            "connection_string", "mongodb://localhost:27017/backo"
        )
        self._collection_name = kwargs.pop("collection", "")

        log.debug("Mongo client to %r", parse_uri(self._connection_string))

        self._db = MongoClient(self._connection_string, **kwargs)

        self._database = self._db.get_default_database()
        self._collection = self._database[self._collection_name]
        DBConnector.__init__(self, **kwargs)

    def connect(self):
        """
        Try to maque a connection to the DB
        """
        try:
            return self._db.server_info()
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error at {self._connection_string}",
            ) from e

    def drop(self):
        """
        Drop the collection
        (used in test)
        """
        log.debug("Drop collection %r", self._collection_name)
        try:
            self._collection.drop()
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.drop() {self._connection_string}",
            ) from e

    def generate_id(self, root):  # pylint: disable=unused-argument
        """
        Do not create _id by ourself. mongo will do the job
        """
        return "666"

    def save(self, _id: str, o: dict):
        """
        Save the object
        """
        o["_id"] = ObjectId(_id)
        try:
            result = self._collection.find_one_and_replace(
                {"_id": ObjectId(_id)}, o, {"upsert": True}
            )
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.find_one_and_replace() {self._connection_string}",
            ) from e
        log.debug("save %r", result)
        return True

    def create(self, o: dict):
        """
        Create the object into the DB and return the _id
        """
        del o["_id"]
        try:
            result = self._collection.insert_one(o)
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.insert_one() {self._connection_string}",
            ) from e
        log.debug("create %r", result.inserted_id)
        return str(result.inserted_id)

    def get_by_id(self, _id: str):
        """
        Read the corresponding file
        """
        log.debug(f"read {_id} ")
        try:
            o = self._collection.find_one({"_id": ObjectId(_id)})
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.find_one() {self._connection_string}",
            ) from e

        if o is None:
            raise Error(ErrorType.NOTFOUND, f'_id "{_id}" not found')
        o["_id"] = _id
        return o

    def delete_by_id(self, _id: str):
        """
        Delete data by Id
        return True if deleted, or False if not found
        """
        log.debug("delete %r", _id)
        try:
            result = self._collection.delete_one({"_id": ObjectId(_id)})
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.delete_one() {self._connection_string}",
            ) from e
        if result.deleted_count == 1:
            return True
        return False

    def select( self, select_filter, projection = {}, page_size = 0, num_of_element_to_skip = 0, sort_object = { '_id' : 1 } ):
        """
        Select and return a list of dicts
        
        select_filter : The fiter
        projection : Fields whe want
        """
        log.debug("select(%r, %r).sort(%r).skip(%r).limit(%r)",
                  select_filter,
                  projection,
                  sort_object,
                  num_of_element_to_skip,
                  page_size)
        try:
            result_list = list(self._collection.find(select_filter, projection).sort(sort_object).skip(num_of_element_to_skip).limit(page_size))
            result_count= self._collection.count_documents(select_filter, skip=num_of_element_to_skip)
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.find() {self._connection_string}",
            ) from e
        return {
            "raw" : result_list,
            "count" : result_count
        }

    def select_short( self, select_filter, short_name, page_size = 0, num_of_element_to_skip = 0, sort_object = { '_id' : 1 } ):
        """
        Select and return a list of dicts
        
        select_filter : The fiter
        projection : Fields whe want
        """
        log.debug("select_short(%r, %r).sort(%r).skip(%r).limit(%r)",
                  select_filter,
                  short_name,
                  sort_object,
                  num_of_element_to_skip,
                  page_size)
        try:
            result_list = list(self._collection.find(select_filter, projection).sort(sort_object).skip(num_of_element_to_skip).limit(page_size))
            result_count= self._collection.count_documents(select_filter, skip=num_of_element_to_skip)
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.find() {self._connection_string}",
            ) from e
        return {
            "raw" : result_list,
            "count" : result_count
        }
