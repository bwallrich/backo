"""
Module providing the Test DB like
"""

# pylint: disable=logging-fstring-interpolation
import os
import sys
import re
import sqlite3

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Kparse

from .db_connector import DBConnector
from .error import NotFoundError, DBError
from .log import log_system


KPARSE_MODEL = {
    "path": {"type": str, "default": "/tmp"}, 
    "dbname": {"type": str, "default": "default"},
    "collection": {"type": str, "default": ""}
}

log = log_system.get_or_create_logger("test")


class DBSQLConnector(DBConnector):  # pylint: disable=too-many-instance-attributes
    """Test SQL Connector

    This is the way to save / store / retrieve objects in yaml files

    :param ``**kwargs``:
        - *path=* ``str`` -- The directory to store yaml files


    """

    def __init__(self, **kwargs):
        """constructor"""

        options = Kparse(kwargs, KPARSE_MODEL)

        self._path = options.get("path")
        self._dbname = options.get("dbname")
        self._collection_name = options.get("collection")

        DBConnector.__init__(self, **kwargs)

        if not os.path.exists(self._path):
            os.makedirs(self._path)

        if not os.path.isdir(self._path):
            raise DBError('SQLLite path "{0}" is not a directory', self._path)

        try:
            self._con = sqlite3.connect(f"{self._path}/{self._dbname}.db")
            self._cursor = self._con.cursor()
        except Exception as e:
            raise DBError(
                'SQLLite connection error at "{0}"', self._path
            ) from e


        # if self.restriction_filter is not None:
        #     raise DBError("Restriction filter not implemented for yml")

    # def connect(self):
    #     try:
    #         self._cursor = self._con.cursor()
    #     except Exception as e:
    #         raise DBError(
    #             'SQLLite connection error at "{0}"', self._path
    #         ) from e

    def _to_sql_type(self, str_type):
        return {
            'String': 'TEXT',
            "Bool": "INTEGER"
        }[str_type]

    def create_table(self, meta):
        str_cols = []
        
        print(f"TABLE {meta["name"]}")

        for col_name, col_data in meta["item"]["sub_scheme"].items():
            if not col_name.startswith("_"):
                col_type = col_data["types"][0]
                str_cols.append(f"{col_name} {self._to_sql_type(col_type)}")
                print(f"COL: {col_name}")
                print(f"TYPE: {col_type}")

        str_request = f"""
        CREATE TABLE IF NOT EXISTS {meta["name"]} (
            id INTEGER PRIMARY KEY, 
            {",".join(str_cols)}
        );
        """
        print(str_request)
        
        try:
            self._cursor.execute(str_request)
            self._con.commit()
            print(self._cursor)

        except sqlite3.OperationalError as e:
            print(f"✗ Operational Error: {e}")
        except sqlite3.IntegrityError as e:
            print(f"✗ Integrity Error: {e}")
        except sqlite3.ProgrammingError as e:
            print(f"✗ Programming Error: {e}")
        except sqlite3.Error as e:
            print(f"✗ Database Error: {e}")
        # finally:

    def drop(self) -> None:
        """See :func:`DBConnector.drop`"""
        try:
            # Delete without condition
            print(self._dbname)
            print(self._path)
            self._cursor.execute(f"DELETE FROM {self._collection_name}")
            self._con.commit()
            
            # Check how many rows were deleted
            deleted_rows = self._cursor.rowcount
            print(f"✓ Deleted {deleted_rows} row(s)")
            
            if deleted_rows == 0:
                print("⚠ Warning: No rows matched the condition")
            
        except sqlite3.OperationalError as e:
            self._con.rollback()
            raise DBError(
                f'✗ Operational Error: {e} while "{self._collection_name}.drop()"'
            ) from e
        except sqlite3.IntegrityError as e:
            print(f"✗ Integrity Error: {e}")
            self._con.rollback()
        except sqlite3.Error as e:
            print(f"✗ Database Error: {e}")
            self._con.rollback()
        # finally:
        #     if conn:
        #         conn.close()


    def save(self, _id: str, o: dict) -> None:
        """See :func:`DBConnector.save`"""
        log.debug(f"save {_id} ")

        try:
            # Insert

            str_request = f'INSERT INTO users (name, surname, male) VALUES ({o["name"]}, {o["surname"]}, TRUE)'
            print(str_request)
            self._cursor.execute()
            self._con.commit()
            
            # Check how many rows were deleted
            # deleted_rows = self._cursor.rowcount
            # print(f"✓ Deleted {deleted_rows} row(s)")
            
            # if deleted_rows == 0:
            #     print("⚠ Warning: No rows matched the condition")
            
        except sqlite3.OperationalError as e:
            self._con.rollback()
            raise DBError(
                f'✗ Operational Error: {e} while "{self._collection_name}.save()"'
            ) from e
        except sqlite3.IntegrityError as e:
            print(f"✗ Integrity Error: {e}")
            self._con.rollback()
        except sqlite3.Error as e:
            print(f"✗ Database Error: {e}")
            self._con.rollback()


    def create(self, o: dict) -> str:
        """See :func:`DBConnector.create`"""
        return -1
        # _id = o["_id"]

        # log.debug(f"create {_id} ")
        # filename = os.path.join(self._path, _id + ".yml")

        # if os.path.exists(filename):
        #     raise DBError('_id "{0}" already exist in path "{1}"', _id, self._path)

        # log.debug(f"try to create {filename}")
        # with open(filename, mode="w", encoding="utf-8") as outfile:
        #     yaml.dump(o, outfile, default_flow_style=False)
        # return _id

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        log.debug(f"read {_id} ")


    def delete_by_id(self, _id: str) -> bool:
        """See :func:`DBConnector.delete_by_id`"""
        log.debug(f"delete {_id}")


    def select(
        self,
        select_filter,
        projection={},
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={"_id": 1},
    ) -> list:
        """See :func:`DBConnector.select`

        Params ``select_filter`` and ``projection`` are not used

        """
        log.debug(
            "select(%r, %r).sort(%r).skip(%r).limit(%r)",
            select_filter,
            projection,
            sort_object,
            num_of_element_to_skip,
            page_size,
        )

        result_list = []

        return result_list

    def close(self):
        """Close the SQLLite connection

        :raise DBError: Raise an error in case of database Error

        """
        try:
            return self._con.close()
        except Exception as e:
            raise DBError('SQLLite close error at "{0}"', self._path) from e
