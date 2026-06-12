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
# from .api_toolbox import append_path_to_filter

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

    # Note: just for test,
    # must use prepared queries to avoid this !
    def _escape_sql_string(self, s):
        """Escape SQL special characters using translation table"""
        trans_table = str.maketrans({
            "'": "''",
            '"': '""',
            "\\": "\\\\",
            "\0": "\\0",
            "\n": "\\n",
            "\r": "\\r",
            "\x1a": "\\Z",
        })
        return s.translate(trans_table)

    def __init__(self, **kwargs):
        """constructor"""

        options = Kparse(kwargs, KPARSE_MODEL)

        self._path = options.get("path")
        self._dbname = options.get("dbname")
        self._collection_name = options.get("collection")
        self._meta = self._flatten_meta(options.get("meta"))
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
            self._con.row_factory = sqlite3.Row
            self._cursor = self._con.cursor()
        except Exception as e:
            raise DBError('SQLLite connection error at "{0}"', self._path) from e

    def get_at_path(self, path, d: dict):
        """
        Get value of a dict at given JSON path
        Note: Just a simple implementation to quick test, but does not support array !
        """
        clean_path = path[2:]
        chunks = clean_path.split(".")
        v = d
        for c in chunks:
            if c in v:
                v = v[c]
            else:
                return None

        return v

    def set_at_path(self, path, d: dict, value):
        """
        Set value of a dict at given JSON path
        Note: Just a simple implementation to quick test, but does not support array !
        """
        clean_path = path[2:]
        chunks = clean_path.split(".")
        v = d

        # Navigate to the parent of the target key
        for c in chunks[:-1]:
            if c not in v:
                v[c] = {}
            v = v[c]

        # Set the value at the final key
        if chunks:
            v[chunks[-1]] = value

    def _flatten_meta(self, meta):
        """
        Flatten metadata to get all nested fields at the same level,
        key becomes the field path instead of field name
        """
        def _rec_flatten_meta(meta, flat_meta):
            for col_name, col_data in meta["sub_scheme"].items():
                types = col_data["types"]

                if "Dict" in types:
                    _rec_flatten_meta(col_data, flat_meta)
                else:
                    if "sub_scheme" not in flat_meta:
                        flat_meta["sub_scheme"] = {}
                    # flat_meta["sub_scheme"][col_name] = col_data
                    flat_meta["sub_scheme"][col_data["path"]] = col_data
                    flat_meta["sub_scheme"][col_data["path"]]["name"] = col_name

            return flat_meta

        flat_meta = {}
        for coll_name, coll_meta in meta.items():
            flat_meta[coll_name] = {}
            _rec_flatten_meta(coll_meta, flat_meta[coll_name])

        return flat_meta

    def _to_sql_type(self, str_type : str) -> str:
        """
        Convert stricto type (string) to SQL type
        Note: Non exhaustive !
        """
        return {
            "String": "TEXT",
            "Bool": "INTEGER",
            "Int": "INTEGER",
            "Float": "REAL",
            "Datetime": "INTEGER",
            "Ref": "TEXT",
        }[str_type]

    def _is_many_many_relationship(self, col_data):
        """
        Check whether given col is a many-many relationship
        """
        col_type = col_data["types"][0]
        if col_type != "RefsList":
            return False

        rev_coll = col_data["collection"]
        rev_col = col_data["reverse"]
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

    def _many_many_table_structure(self, col_path, col_data):
        """
        Generate name and column mapping for an intermediate many-to-many join table.
        """
        # 1. Extract and clean the collection names and fields
        source_coll = self._collection_name
        target_coll = col_data["collection"]

        # If it's a fixed prefix, consider using .lstrip() or .removeprefix() instead of slicing
        target_col_name = col_data["reverse"]
        source_col_name = col_path

        # 2. Determine a deterministic order so TableA->TableB and TableB->TableA resolve identically
        # We pack the related entities into standardized pairs
        sources = (source_coll, source_col_name)
        targets = (target_coll, target_col_name)

        # Sort lexicographically based on the collection names
        first_side, second_side = sorted([sources, targets], key=lambda x: x[0])

        # 3. Construct the table name cleanly
        col = first_side[1].replace("$.", "").replace(".", "_")
        table_name = f"{first_side[0]}_{col}_{second_side[0]}"

        return {
            "col_name": col_path,
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
        """
        # Get data of intermediate table
        table_data = col_data["join_table"]
        return f"""
        CREATE TABLE IF NOT EXISTS {table_data['name']} (
            '{table_data['source_col']}' TEXT ,
            '{table_data['target_col']}' TEXT ,
            FOREIGN KEY ('{table_data['source_col']}') REFERENCES {table_data['source_coll']}(_id) ,
            FOREIGN KEY ('{table_data['target_col']}') REFERENCES {table_data['target_coll']}(_id) ,
            PRIMARY KEY ('{table_data['source_col']}', '{table_data['target_col']}')
        );
        """

    def create_table(self):
        """
        Create table from the collection schema
        """
        str_cols = []

        for col_path, col_data in self._scheme.items():
            col_type = col_data["types"][0]
            if not col_type == "RefsList":
                str_cols.append(f"'{col_path}' {self._to_sql_type(col_type)}")

        # Add one-many relationship
        for col_path, col_data in self._scheme.items():
            col_type = col_data["types"][0]
            if col_type == "Ref":
                str_cols.append(
                    # f"FOREIGN KEY ({col_name}) REFERENCES {col_data["collection"]}(_id)"
                    f"FOREIGN KEY ('{col_path}') REFERENCES {col_data["collection"]}(_id)"
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

    def _format_val(self, val) -> str:
        """
        Format value to SQL string according to its type
        """
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        if isinstance(val, str):
            return f"'{self._escape_sql_string(val)}'"

        return str(val)

    def _map_val(self, val, target_types):
        """
        Map a value according to given target type
        """
        if "Bool" in target_types:
            return bool(val)
        if "Int" in target_types:
            return int(val)

        return val

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

            # Collect column names and values in a single pass
            col_names = []
            col_values = []

            for col_path, col_data in self._scheme.items():
                val = self.get_at_path(col_path, o)
                # Exclude RefsList for insert
                if val is not None and "RefsList" not in col_data["types"]:
                    col_names.append(col_path)
                    col_values.append(val)

            # Build prepared query
            str_col_names = ",".join(f'"{col_name}"' for col_name in col_names)
            placeholders = ",".join("?" * len(col_values))
            str_request = f"INSERT INTO {self._collection_name} ({str_col_names}) VALUES ({placeholders})"

            # Execute with values passed separately
            log.debug(f"Execute: {str_request}")
            self._cursor.execute(str_request, col_values)

            # Insert many-many relationships in intermediate table
            for col_path, col_data in self._scheme.items():
                if self._is_many_many_relationship(col_data):
                    col_data = self._many_many_table_structure(col_path, col_data)
                    val = self.get_at_path(col_path, o)
                    if val is not None:
                        for dst_id in val:
                            table_data = col_data["join_table"]
                            # Note that here we can insert multiple rows in single operation (more effective)
                            str_request = f"INSERT INTO {table_data['name']} ('{col_path}', '{col_data['rev_col_name']}') VALUES ('{dst_id}', '{_id}')"
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
        o = {}
        for col_name, col_data in self._scheme.items():
            col_types = col_data["types"]

            row_dict = dict(row)
            if col_name in row_dict and "RefsList" not in col_types:
                val = row[col_name]
                if val:
                    map_val = self._map_val(row[col_name], col_types)
                    self.set_at_path(col_name, o, map_val)

        return o

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        log.debug(f"read {_id} ")

        def select():
            # Create and execute request using prepared query
            str_request = (
                f"SELECT * FROM {self._collection_name} WHERE \"$._id\"=?"
            )
            log.debug(f"Execute: {str_request}")
            self._cursor.execute(str_request, (_id,))
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
                str_request = f"SELECT join_table.\"{col_data['col_name']}\" \
                    FROM {table_data['name']} join_table \
                    INNER JOIN {self._collection_name} cur \
                    ON cur.\"$._id\" = join_table.\"{col_data['rev_col_name']}\" \
                    WHERE cur.\"$._id\" = '{_id}'"

                log.debug(f"Execute: {str_request}")
                self._cursor.execute(str_request)

                col_path = col_data["col_name"]

                self.set_at_path(
                    col_path,
                    o,
                    [
                        self._map_val(row[col_path], col_types)
                        for row in self._cursor.fetchall()
                    ],
                )

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
