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

    def drop_table(self):
        """
        Drop tables for current collection
        """

        # Stack queries
        str_requests = [f"DROP TABLE IF EXISTS {self._collection_name}"]
        str_requests += [
            f"DROP TABLE IF EXISTS {col_data["join_table"]["name"]}"
            for col_data in self._get_many_to_many_cols_data()
        ]

        def drop_table_execute():
            # Execute all stacked queries
            for str_request in str_requests:
                log.debug(f"Execute: {str_request}")
                self._cursor.execute(str_request)

            self._con.commit()
            log.debug(f"✓ Dropped tables of {self._collection_name}")

        return self._sqlite_try(drop_table_execute)

    def create_table(self):
        """
        Create tables for current collection
        """

        # 1. Build create table query
        # Add scalar cols
        str_cols = [
            f"'{col_name}' {self._to_sql_type(col_data["types"][0])}"
            for col_name, col_data in self._get_scalar_cols()
        ]
        # Add one-many relationship
        str_cols += [
            f"FOREIGN KEY ('{col_name}') REFERENCES {col_data["collection"]}(_id)"
            for col_name, col_data in self._get_one_to_many_cols_data()
        ]

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
            for col_data in self._get_many_to_many_cols_data()
        ]

        for str_request in str_requests:
            self._sqlite_try(create_table_execute)

    def drop(self) -> None:
        """See :func:`DBConnector.drop`"""

        # Build list of table names to delete from
        table_names = [
            col_data["join_table"]["name"]
            for col_data in self._get_many_to_many_cols_data()
        ]
        # Add current collection table (must be last to respect foreign keys)
        table_names.append(self._collection_name)

        def delete_all():
            # Stack all DELETE queries before executing
            delete_queries = []
            for table_name in table_names:
                str_request = f"DELETE FROM {table_name}"
                delete_queries.append(str_request)

            # Execute all stacked queries
            deleted_count = 0
            for str_request in delete_queries:
                log.debug(f"Execute: {str_request}")
                self._cursor.execute(str_request)
                deleted_count += self._cursor.rowcount

            # Commit all deletions
            self._con.commit()

            log.debug(f"✓ Deleted {deleted_count} row(s)")

            if deleted_count == 0:
                log.warning("No rows matched the condition")

        # Execute with error handling
        self._sqlite_try(delete_all)

    def save(self, _id: str, o: dict) -> None:
        """See :func:`DBConnector.save`"""
        log.debug(f"save {_id} ")

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
            # Stack all INSERT queries before executing

            # 1. Collect main record insert query
            scalar_cols = [
                (col_path, self.get_at_path(col_path, o))
                for col_path, col_data in self._scheme.items()
                if (val := self.get_at_path(col_path, o)) is not None
                and not self._is_ref_list(col_data)
            ]
            col_names = [col_path for col_path, _ in scalar_cols]
            col_values = [val for _, val in scalar_cols]

            # Build main record insert query
            str_col_names = ",".join(f'"{col_name}"' for col_name in col_names)
            placeholders = ",".join("?" * len(col_values))
            main_insert = (
                f"INSERT INTO {self._collection_name} ({str_col_names}) VALUES ({placeholders})",
                col_values,
            )

            # 2. Collect many-many relationship insert queries
            many_many_inserts = []
            for col_data in self._get_many_to_many_cols_data():
                col_name = col_data["col_name"]
                val = self.get_at_path(col_name, o)

                if val is None:
                    continue

                table_data = col_data["join_table"]
                table_name = table_data["name"]
                rev_col_name = col_data["rev_col_name"]

                # Prepare batch data: (dst_id, _id) for each relationship
                batch_data = [(dst_id, _id) for dst_id in val]

                # Build many-many insert query
                str_request = f'INSERT INTO {table_name} ("{col_name}", "{rev_col_name}") VALUES (?, ?)'
                many_many_inserts.append((str_request, batch_data))

            # Execute all stacked queries
            # Main record insert first
            str_request, col_values = main_insert
            log.debug(f"Execute: {str_request}")
            self._cursor.execute(str_request, col_values)

            # Many-many relationship inserts
            for str_request, batch_data in many_many_inserts:
                log.debug(f"Execute: {str_request}")
                self._cursor.executemany(str_request, batch_data)

            # Commit all requests
            self._con.commit()
            log.debug(f"✓ Created {self._collection_name} {_id}")

            return _id

        return self._sqlite_try(insert)

    def get_by_id(self, _id: str) -> dict:
        """See :func:`DBConnector.get_by_id`"""
        log.debug(f"read {_id}")

        def select():
            # Execute main record query
            query = f'SELECT * FROM {self._collection_name} WHERE "$._id"=?'
            log.debug(f"Execute: {query}")
            self._cursor.execute(query, (_id,))
            row = self._cursor.fetchone()

            # No results!
            if row is None:
                raise NotFoundError(
                    '_id "{0}" not found in collection "{1}"',
                    _id,
                    self._collection_name,
                )

            # Map row result to object
            o = self._map_row(row)

            # Stack all many-to-many queries before executing
            queries = []
            for col_data in self._get_many_to_many_cols_data():
                query, params = self._build_many_to_many_query(col_data, _id)
                queries.append((query, params, col_data))

            # Stack all many-to-one queries before executing
            for col_data in self._get_many_to_one_cols_data():
                query, params = self._build_many_to_one_query(col_data, _id)
                queries.append((query, params, col_data))

            # Execute all stacked many-to-many queries
            refs_results = []
            for query, params, col_data in queries:
                log.debug(self._collection_name)
                log.debug(f"Execute: {query} with params {params}")
                self._cursor.execute(query, params)
                rows = self._cursor.fetchall()
                refs_results.append((col_data, rows))

            # Map all RefsList results to object
            for col_data, rows in refs_results:
                col_name = col_data["col_name"]
                col_types = col_data["data"]["types"]

                mapped_values = [
                    self._map_val(row[col_name], col_types) for row in rows
                ]

                self.set_at_path(col_name, o, mapped_values)

            log.debug(f"✓ GetById {self._collection_name} {_id}")

            return o

        return self._sqlite_try(select)

    def delete_by_id(self, _id: str) -> bool:
        """See :func:`DBConnector.delete_by_id`"""
        log.debug(f"delete {_id}")

        def delete_record():
            # Stack all DELETE queries before executing
            delete_queries = []

            # Stack join table deletions
            for col_data in self._get_many_to_many_cols_data():
                table_name = col_data["join_table"]["name"]
                rev_col_name = col_data["rev_col_name"]

                str_request = f'DELETE FROM {table_name} WHERE "{rev_col_name}" = ?'
                delete_queries.append((str_request, (_id,)))

            # Stack main record deletion (must be last to respect foreign keys)
            str_request = f'DELETE FROM {self._collection_name} WHERE "$._id" = ?'
            delete_queries.append((str_request, (_id,)))

            # Execute all stacked queries
            deleted_count = 0
            for str_request, params in delete_queries:
                log.debug(f"Execute: {str_request}")
                self._cursor.execute(str_request, params)
                deleted_count += self._cursor.rowcount

            # Commit all deletions
            self._con.commit()

            log.debug(f"✓ Deleted {deleted_count} row(s)")

            return deleted_count > 0

        # Execute with error handling and return result
        return self._sqlite_try(delete_record)

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

    # --- Columns & meta utils functions ---

    def _is_ref_list(self, col_data):
        return "RefsList" in col_data["types"]

    def _is_many_to_many(self, col_data):
        """
        Check whether given col is a many-many relationship
        """
        if "RefsList" not in col_data["types"]:
            return False

        rev_coll = col_data["collection"]
        rev_col = col_data["reverse"]
        return "RefsList" in self._meta[rev_coll]["sub_scheme"][rev_col]["types"]

    def _is_many_to_one(self, col_data):
        """
        Check whether given col is a many-one relationship
        """
        if "RefsList" not in col_data["types"]:
            return False

        rev_coll = col_data["collection"]
        rev_col = col_data["reverse"]
        return "Ref" in self._meta[rev_coll]["sub_scheme"][rev_col]["types"]

    def _get_scalar_cols(self):
        """
        Filter & get only Ref / RefsList cols
        """
        return [
            (col_name, col_data)
            for col_name, col_data in self._scheme.items()
            if not self._is_ref_list(col_data)
        ]

    def _get_one_to_many_cols_data(self):
        """
        Filter & get only Ref cols
        """
        return [
            (col_name, col_data)
            for col_name, col_data in self._scheme.items()
            if "Ref" in col_data["types"]
        ]

    def _get_many_to_many_cols_data(self):
        """
        Filter & get only RefsList - RefsList cols
        """
        return [
            self._many_to_many_data(col_name, col_data)
            for col_name, col_data in self._scheme.items()
            if self._is_many_to_many(col_data)
        ]

    def _get_many_to_one_cols_data(self):
        """
        Filter & get only RefsList - Ref cols
        """
        return [
            {
                "col_name": col_name,
                "data": col_data,
                "rev_col_name": col_data["reverse"],
                "join_table": {"name": col_data["collection"]},
            }
            for col_name, col_data in self._scheme.items()
            if self._is_many_to_one(col_data)
        ]

    def _many_to_many_data(self, col_name, col_data):
        """
        Generate name and column mapping for an intermediate many-to-many join table.
        """
        # 1. Extract and clean the collection names and fields
        source_coll = self._collection_name
        target_coll = col_data["collection"]

        # If it's a fixed prefix, consider using .lstrip() or .removeprefix() instead of slicing
        target_col_name = col_data["reverse"]
        source_col_name = col_name

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

    # --- SQL utils functions ---

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

    def _build_many_to_many_query(self, col_data: dict, _id: str):
        """Build and return prepared query + params for fetching many to many data"""
        table_name = col_data["join_table"]["name"]
        col_name = col_data["col_name"]
        rev_col_name = col_data["rev_col_name"]

        query = f"""
            SELECT join_table."{col_name}"
            FROM {table_name} join_table
            INNER JOIN {self._collection_name} cur
            ON cur."$._id" = join_table."{rev_col_name}"
            WHERE cur."$._id" = ?
        """
        return query, (_id,)

    def _build_many_to_one_query(self, col_data: dict, _id: str):
        """Build and return prepared query + params for fetching many to one data"""
        table_name = col_data["join_table"]["name"]
        col_name = col_data["col_name"]
        rev_col_name = col_data["rev_col_name"]

        query = f"""
            SELECT rev.\"$._id\" AS \"{col_name}\"
            FROM {table_name} rev
            INNER JOIN {self._collection_name} cur
            ON rev.\"{rev_col_name}\" = cur.\"$._id\"
            WHERE cur.\"$._id\" = ?
        """
        return query, (_id,)

    def _map_val(self, val, target_types):
        """
        Map a value according to given target type
        """
        if "Bool" in target_types:
            return bool(val)
        if "Int" in target_types:
            return int(val)

        return val

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

    def _to_sql_type(self, str_type: str) -> str:
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

    # --- Dict utils functions ---
    # Note: some utils functions, just for test, not production ready !
    # Should not be in this class...

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
