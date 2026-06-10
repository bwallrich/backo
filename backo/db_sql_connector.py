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
    "meta": {"type": dict},
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
        self._meta = options.get("meta")
        self._scheme = self._meta[self._collection_name][
            "sub_scheme"
        ]  # Shortcut to data

        # Add shortcut to fields (extracted from scheme)
        # Add shortcut to one-many (extracted from scheme)
        # Add shortcut to many-many (extracted from scheme)

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

    def _flatten_meta(self, meta):

        def _rec_flatten_meta(meta, flat_meta):
            for col_name, col_data in meta["sub_scheme"].items():
                types = col_data["types"]

                if "Dict" in types:
                    print(f"FOUND DICT: {col_name}" )
                    _rec_flatten_meta(col_data, flat_meta)
                else:
                    if "sub_scheme" not in flat_meta:
                        flat_meta["sub_scheme"] = {}
                    flat_meta["sub_scheme"][col_name] = col_data
            
            return flat_meta

        flat_meta = {}
        for coll_name, coll_meta in meta.items():    
            flat_meta[coll_name] = {}
            print(f"PARSE {coll_name}")
            _rec_flatten_meta(coll_meta, flat_meta[coll_name])

        return flat_meta

    def _to_sql_type(self, str_type):
        return {"String": "TEXT", "Bool": "INTEGER", "Ref": "TEXT"}[str_type]

    def _is_many_many_relationship(self, col_data):
        """
        Check whether given col is a many-many relationship
        """
        col_type = col_data["types"][0]
        if col_type != "RefsList":
            return False

        rev_coll = col_data["collection"]
        rev_col = col_data["reverse"][
            2:
        ]  # Tricky for now need to select actual field $.my.path.to
        return "RefsList" in self._meta[rev_coll]["sub_scheme"][rev_col]["types"]

    def _get_many_many_cols(self):
        """
        Loop over all columns of collection item and call the
        callback function for columns that are many-many relationship
        then stack results into a generator
        """
        for col_name, col_data in self._scheme.items():
            if self._is_many_many_relationship(col_data):
                yield self._many_many_table_structure(col_name, col_data)

    def _many_many_table_structure(self, col_name, col_data):
        """
        Generate name and column mapping for an intermediate many-to-many join table.
        """
        # 1. Extract and clean the collection names and fields
        source_coll = self._collection_name
        target_coll = col_data["collection"]

        # If it's a fixed prefix, consider using .lstrip() or .removeprefix() instead of slicing
        target_col_name = col_data["reverse"][2:]
        source_col_name = col_name

        # 2. Determine a deterministic order so TableA->TableB and TableB->TableA resolve identically
        # We pack the related entities into standardized pairs
        sources = (source_coll, source_col_name)
        targets = (target_coll, target_col_name)

        # Sort lexicographically based on the collection names
        first_side, second_side = sorted([sources, targets], key=lambda x: x[0])

        # 3. Construct the table name cleanly
        table_name = f"{first_side[0]}_{first_side[1]}_{second_side[0]}"

        return {
            "col_name": col_name,
            "data": col_data,
            "rev_col_name": target_col_name,
            "join_table": {
                "name": table_name,
                "source_coll": first_side[0],
                "target_coll": second_side[0],
                "source_col": second_side[1],
                "target_col": first_side[1],
            },
        }

    def _build_join_table_request(self, col_data):
        """
        Generate the SQL query to create an intermediate join table for a
        many-to-many relationship.

        Args:
            table_structure (tuple): A 5-element tuple containing:
                (table_name, source_coll, target_coll, source_col_name, target_col_name)

        Returns:
            str: A raw SQL 'CREATE TABLE' query string.
        """
        # Get data of intermediate table
        table_data = col_data["join_table"]
        return f"""
        CREATE TABLE IF NOT EXISTS {table_data['name']} (
            {table_data['source_col']} TEXT ,
            {table_data['target_col']} TEXT ,
            FOREIGN KEY ({table_data['source_col']}) REFERENCES {table_data['source_coll']}(_id) ,
            FOREIGN KEY ({table_data['target_col']}) REFERENCES {table_data['target_coll']}(_id) ,
            PRIMARY KEY ({table_data['source_col']}, {table_data['target_col']})
        );
        """

    def create_table(self):
        """
        Create table from the collection schema
        """
        str_cols = []

        for col_name, col_data in self._scheme.items():
            col_type = col_data["types"][0]
            if not col_name.startswith("_") and not col_type == "RefsList":
                str_cols.append(f"{col_name} {self._to_sql_type(col_type)}")

        # Add one-many relationship
        for col_name, col_data in self._scheme.items():
            col_type = col_data["types"][0]
            if col_type == "Ref":
                str_cols.append(
                    f"FOREIGN KEY ({col_name}) REFERENCES {col_data["collection"]}(_id)"
                )

        str_request = f"""
        CREATE TABLE IF NOT EXISTS {self._collection_name} (
            _id TEXT PRIMARY KEY, 
            {",".join(str_cols)}
        );
        """

        def create_table_execute():
            log.debug(f"Execute: {str_request}")
            self._cursor.execute(str_request)
            self._con.commit()

        self._sqlite_try(create_table_execute)

        # Generate intermediate tables (many-many relationships)
        str_requests = [
            self._build_join_table_request(col_data)
            for col_data in self._get_many_many_cols()
        ]

        for str_request in str_requests:
            log.debug(f"Execute: {str_request}")
            self._sqlite_try(create_table_execute)

    def drop(self) -> None:
        """See :func:`DBConnector.drop`"""

        # Function to create SQL request string
        def build_delete_request(table_name):
            return f"DELETE FROM {table_name}"

        # For each many-many field, build a delete request on join table
        str_requests = [
            build_delete_request(col_data["join_table"]["name"])
            for col_data in self._get_many_many_cols()
        ]
        # Add request for deleting all elements in table of current collection without condition
        str_requests.append(build_delete_request(self._collection_name))

        # Execute and commit delete requests
        def delete_all():
            # Execute all delete requests
            for str_request in str_requests:
                log.debug(f"Execute: {str_request}")
                self._cursor.execute(str_request)

            # Commit !
            self._con.commit()

            # Check how many rows were deleted
            deleted_rows = self._cursor.rowcount
            log.debug(f"✓ Deleted {deleted_rows} row(s)")

            if deleted_rows == 0:
                log.warning("No rows matched the condition")

        # Effectively try to execute SQL requests
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

    def _map_val(self, val, target_types):
        if "Bool" in target_types:
            return bool(val)
        if "Int" in target_types:
            return int(val)

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
        # Generate new id and set to object
        # Note: doesn't support integer & auto increment id for now
        _id = self.generate_id(o)
        o["_id"] = _id

        log.debug(f"create {_id} ")

        def insert():

            t = []
            for col_name, col_data in self._scheme.items():
                # Exclude RefsList and _meta columns for insert
                if "RefsList" not in col_data["types"] and col_name != "_meta":
                    t.append((col_name, self._format_val(o[col_name])))

            str_col_names = ",".join(field_name for field_name, _ in t)
            str_values = ",".join(field_value for _, field_value in t)

            str_request = f"INSERT INTO {self._collection_name} ({str_col_names}) VALUES ({str_values})"

            # Insert
            log.debug(f"Execute: {str_request}")
            self._cursor.execute(str_request)

            # Insert many-many relationships in intermediate table
            for col_name, col_data in self._scheme.items():
                if self._is_many_many_relationship(col_data):
                    col_data = self._many_many_table_structure(col_name, col_data)
                    for dst_id in o[col_name]:
                        table_data = col_data["join_table"]
                        # Note that here we can insert multiple rows in single operation (more effective)
                        str_request = f"INSERT INTO {table_data['name']} ({col_data['col_name']}, {col_data['rev_col_name']}) VALUES ('{dst_id}', '{_id}')"
                        log.debug(f"Execute: {str_request}")
                        self._cursor.execute(str_request)

            # Commit all requests
            self._con.commit()
            log.debug(f"✓ Created {self._collection_name} {_id}")

            return _id

        return self._sqlite_try(insert)

    def _map_row(self, row):
        """
        Map a row result from SQL to an object
        """
        # Create object
        # id is always the first column of the row
        o = {"_id": row[0]}

        for i, (col_name, col_data) in enumerate(self._scheme.items()):
            col_types = col_data["types"]
            if "RefsList" not in col_types and not col_name.startswith("_"):
                o[col_name] = self._map_val(row[i + 1], col_types)

        return o

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        log.debug(f"read {_id} ")

        def select():
            # Create and execute request
            str_request = f"SELECT * FROM {self._collection_name} WHERE _id='{_id}'"
            log.debug(f"Execute: {str_request}")
            self._cursor.execute(str_request)
            row = self._cursor.fetchone()

            # No results !
            if row is None:
                raise NotFoundError(
                    '_id "{0}" not found in collection "{1}"',
                    _id,
                    self._collection_name,
                )

            # Map row result to object
            o = self._map_row(row)

            # Retrieve RefsList ids
            for col_data in self._get_many_many_cols():
                col_types = col_data["data"]["types"]
                table_data = col_data["join_table"]
                str_request = f"SELECT join_table.{col_data['col_name']} FROM {table_data['name']} join_table INNER JOIN {self._collection_name} cur ON cur._id = join_table.{col_data['rev_col_name']} WHERE cur._id = '{_id}'"
                log.debug(f"Execute: {str_request}")
                self._cursor.execute(str_request)
                o[col_data["col_name"]] = [
                    self._map_val(row[0], col_types) for row in self._cursor.fetchall()
                ]

            log.debug(f"✓ GetById {self._collection_name} {_id}")

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
