"""
Module providing the Test DB like
"""

# pylint: disable=logging-fstring-interpolation
import os
import sys
import sqlite3

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Kparse

from .db_connector import DBConnector
from .error import NotFoundError
from .error import DBError
from .log import log_system

KPARSE_MODEL = {
    "path": {"type": str, "default": "/tmp"},
    "dbname": {"type": str, "default": "default"},
    "collection": {"type": str, "default": ""},
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
            raise DBError('SQLLite connection error at "{0}"', self._path) from e

    def _to_sql_type(self, str_type):
        return {"String": "TEXT", "Bool": "INTEGER", "Ref": "TEXT"}[str_type]

    def create_table(self, meta):
        """
        Table creation from schema
        """
        str_cols = []

        for col_name, col_data in meta["sub_scheme"].items():
            col_type = col_data["types"][0]
            if not col_name.startswith("_") and not (col_type == "RefsList"):
                str_cols.append(f"{col_name} {self._to_sql_type(col_type)}")


        # Add one-many relationship
        for col_name, col_data in meta["sub_scheme"].items():
            col_type = col_data["types"][0]
            if (col_type == "Ref"):
                str_cols.append(f"FOREIGN KEY ({col_name}) REFERENCES {col_data["collection"]}(_id)")
                # str_alter_request = f"ALTER TABLE {self._collection_name} ADD CONSTRAINT FK_{self._collection_name}_{col_name} FOREIGN KEY ({col_name}_id) REFERENCES {col_name}(_id)"
                print(str_cols)

        str_request = f"""
        CREATE TABLE IF NOT EXISTS {self._collection_name} (
            _id TEXT PRIMARY KEY, 
            {",".join(str_cols)}
        );
        """

        print(str_request)




        def create_table_execute():
            self._cursor.execute(str_request)
            self._con.commit()
            self._meta = meta

        self._sqlite_try(create_table_execute)

    def drop(self) -> None:
        """See :func:`DBConnector.drop`"""

        def delete_all():
            # Delete without condition
            self._cursor.execute(f"DELETE FROM {self._collection_name}")
            self._con.commit()

            # Check how many rows were deleted
            deleted_rows = self._cursor.rowcount
            print(f"✓ Deleted {deleted_rows} row(s)")

            if deleted_rows == 0:
                print("⚠ Warning: No rows matched the condition")

        self._sqlite_try(delete_all)

    def save(self, _id: str, o: dict) -> None:
        """See :func:`DBConnector.save`"""
        log.debug(f"save {_id} ")

    def _format_val(self, val):
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        if isinstance(val, str):
            return f"'{val}'"

        return val

    def _map(self, val, target_types):
        if "Bool" in target_types:
            return bool(val)

        return val

    def _is_internal_field(self, field):
        return field.startswith("_")

    def _sqlite_try(self, callback):
        """
        Just a function to factorize
        the catching of sqlite exceptions
        """
        try:
            return callback()
        except sqlite3.OperationalError as e:
            self._con.rollback()
            raise DBError(
                f'✗ Operational Error: {e} while "{self._collection_name}.create()"'
            ) from e
        except sqlite3.IntegrityError as e:
            self._con.rollback()
            raise DBError(
                f'✗ Integrity Error: {e} while "{self._collection_name}.create()"'
            ) from e
        except sqlite3.Error as e:
            self._con.rollback()
            raise DBError(
                f'✗ Database Error: {e} while "{self._collection_name}.create()"'
            ) from e

    def create(self, o: dict) -> str:
        """See :func:`DBConnector.create`"""
        _id = self.generate_id(o)
        o["_id"] = _id

        log.debug(f"create {_id} ")

        def insert():

            t = []
            for col_name, col_data in self._meta["sub_scheme"].items():
                col_types = col_data["types"]
                if "RefsList" not in col_types and col_name != "_meta":
                    t.append((col_name, self._format_val(o[col_name])))
            
            str_col_names = ",".join(field_name for field_name, _ in t)
            str_values = ",".join(field_value for _, field_value in t)

            print(str_col_names)
            print(str_values)

            str_request = f"INSERT INTO {self._collection_name} ({str_col_names}) VALUES ({str_values})"

            # Insert
            self._cursor.execute(str_request)
            self._con.commit()

            log.debug(f"✓ Created {self._collection_name} {_id}")

            return _id

        return self._sqlite_try(insert)

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        log.debug(f"read {_id} ")

        def select():
            str_request = f"SELECT * FROM {self._collection_name} WHERE _id='{_id}'"
            print(str_request)
            self._cursor.execute(str_request)
            row = self._cursor.fetchone()

            if row is None:
                raise NotFoundError(
                    '_id "{0}" not found in collection "{1}"',
                    _id,
                    self._collection_name,
                )

            log.debug(f"✓ GetById {self._collection_name} {_id}")

            o = {"_id": row[0]}
            for i, (col_name, col_data) in enumerate(self._meta["sub_scheme"].items()):
                col_types = col_data["types"]
                if "RefsList" not in col_types and not col_name.startswith("_"):
                    o[col_name] = self._map(row[i + 1], col_data["types"])

            return o

        return self._sqlite_try(select)

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
