"""
Module providing the mongo DB like
"""

# pylint: disable=logging-fstring-interpolation
import logging
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri
from bson.objectid import ObjectId

from .db_connector import DBConnector
from .error import Error, ErrorType
from .log import log_system

log = log_system.get_or_create_logger("mongo")
log.setLevel(logging.INFO)


class DBMongoConnector(DBConnector):  # pylint: disable=too-many-instance-attributes
    """Mongodb database Connector

    This is the way to save / store / retrieve objects in a mongodb

    :param ``**kwargs``:
        - *restriction=* ``func`` -- not used yet
        - all other params are passed to ``Mongoclient``


    """

    def __init__(self, **kwargs):
        """constructor"""
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
        """Try to make a connection to the mongodb

        :raise Error: Raise an error ErrorType.MONGO_CONNECT_ERROR in case of database Error

        """
        try:
            return self._db.server_info()
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error at {self._connection_string}",
            ) from e

    def close(self):
        """Close the mongodb connection

        :raise Error: Raise an error ErrorType.MONGO_CONNECT_ERROR in case of database Error

        """
        try:
            return self._db.close()
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo close error at {self._connection_string}",
            ) from e

    def drop(self):
        """See :func:`DBConnector.drop`

        :raise Error: Raise an error ErrorType.MONGO_CONNECT_ERROR in case of database Error

        """
        log.debug("Drop collection %r", self._collection_name)
        try:
            self._collection.drop()
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.drop() {self._connection_string}",
            ) from e

    def _combine_with_restriction_filter(self, select):
        """
        Combine the filter with the restriction filter (if exists)
        """
        if self.restriction_filter is None:
            return select

        rfilter = (
            self.restriction_filter()
            if callable(self.restriction_filter)
            else self.restriction_filter
        )
        return {"$and": [rfilter, select]}

    def generate_id(self, o):  # pylint: disable=unused-argument
        """Do not create _id by ourself. mongo will do the job"""
        return "666"

    def save(self, _id: str, o: dict):
        """See :func:`DBConnector.save`"""
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
        """See :func:`DBConnector.create`"""
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
        """See :func:`DBConnector.get_by_id`"""
        log.debug(f"try to read {_id} ")
        try:
            db_filter = self._combine_with_restriction_filter({"_id": ObjectId(_id)})
            o = self._collection.find_one(db_filter)
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
        """See :func:`DBConnector.delete_by_id`"""
        log.debug("try to delete %r", _id)
        try:
            db_filter = self._combine_with_restriction_filter({"_id": ObjectId(_id)})
            result = self._collection.delete_one(db_filter)
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.delete_one() {self._connection_string}",
            ) from e
        if result.deleted_count == 1:
            return True
        return False

    def select(
        self,
        select_filter,
        projection={},
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={"_id": 1},
    ):
        """See :func:`DBConnector.select`

        :param select_filter: The filter for selection
        :type select_filter: dict ( a mongodb fliter syntax )


        """
        log.debug(
            "select(%r, %r).sort(%r).skip(%r).limit(%r)",
            select_filter,
            projection,
            sort_object,
            num_of_element_to_skip,
            page_size,
        )

        db_filter = self._combine_with_restriction_filter(select_filter)
        try:
            result_list = list(
                self._collection.find(db_filter, projection)
                .sort(sort_object)
                .skip(num_of_element_to_skip)
                .limit(page_size)
            )
        except Exception as e:
            raise Error(
                ErrorType.MONGO_CONNECT_ERROR,
                f"Mongo connection error while {self._collection_name}.find() {self._connection_string}",
            ) from e
        return result_list
