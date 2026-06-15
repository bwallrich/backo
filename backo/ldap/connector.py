"""
The db_ldap_connector module provides features to use LDAP as a backend
database.
"""

from backo.error import DBError

from ..db_connector import DBConnector
from backo.database.engine import DatabaseEngine


class LdapConnector(DBConnector):
    """
    Implements the abstract DBConnector for LDAP.
    """

    def __init__(
        self,
        database_engine: DatabaseEngine,
    ):
        """Creates a new LdapConnector.

        :param database_engine: Engine used to perform requests on the LDAP
        database
        """
        self.ldap_database_engine = database_engine

    def drop(self):  # pylint: disable=unused-argument
        raise DBError("LdapConnector does not implement drop()")

    def create(self, o: dict) -> str:  # pylint: disable=unused-argument
        raise DBError("LdapConnector does not implement create()")

    def save(self, _id: str, o: dict):  # pylint: disable=unused-argument
        raise DBError("LdapConnector does not implement save()")

    def delete_by_id(self, _id: str):  # pylint: disable=unused-argument
        raise DBError("LdapConnector does not implement delete_by_id()")

    def get_by_id(self, _id: str) -> dict:
        return self.ldap_database_engine.search(_id)

    def select(
        self,
        select_filter,
        projection={},
        page_size=0,
        num_of_element_to_skip=0,
        sort_object={"_id": 1},
    ) -> list:
        raise DBError("LdapConnector does not implement select()")
