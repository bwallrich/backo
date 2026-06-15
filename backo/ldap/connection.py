import ldap3

from typing import Any
from backo.error import NotFoundError
from .request import LdapSearchRequest


class LdapConnection:
    def __init__(self, ldap_connection: ldap3.Connection):
        """Creates a new LdapConnection.

        See the [ldap3
        documention](https://ldap3.readthedocs.io/en/latest/connection.html#)
        for how to init the LDAP connection. Common examples:
        - LDAP connection without TLS
          ```python
          ldap_server = ldap3.Server("ldap://ldap.example.org")
          ldap_connection = ldap3.Connection(
              ldap_server,
              "username",
              "password",
              auto_bind=True
          )
          ```
        - LDAP connection with TLS
          ```python
          ldap_server = ldap3.Server(
              "ldaps://ldap.example.org",
              use_ssl=True
            )
          ldap_connection = ldap3.Connection(
              ldap_server,
              "username",
              "password",
              auto_bind=True
          )
          ```
        - LDAP connection with TLS and a custom CA
          ```python
          ldap_server = ldap3.Server(
            "ldaps://ldap.example.org",
            use_ssl=True,
            tls=ldap3.Tls(ca_certs_file="/path/to/custom/ca.crt")
          )
          ldap_connection = ldap3.Connection(
              ldap_server,
              "username",
              "password",
              auto_bind=True
          )
          ```

        :param ldap_connection: An ldap3.Connection instance used to perform
        LDAP operations
        """
        self.ldap_connection = ldap_connection

    def execute_search(
        self, ldap_search_request: LdapSearchRequest
    ) -> list[dict[str, Any]]:
        """Performs an LDAP SEARCH operation with parameters of the
        ldap_search_request.

        The response is formatted as specified in the [ldap3
        documentation](https://ldap3.readthedocs.io/en/latest/searches.html#response).
        It is a list of LDAP entries, each of which is represented by a dict
        containing "dn" and "attributes" keys. The value associated to
        "attributes" is itself a dict mapping LDAP attributes name to their
        values, formatted according to the current LDAP schemas.

        :param ldap_search_request: LDAP search parameters
        """

        self.ldap_connection.search(
            ldap_search_request.search_base,
            ldap_search_request.search_filter,
            attributes=ldap_search_request.attributes,
        )

        ldap_response = []
        try:
            ldap_response = self.ldap_connection.response
        except IndexError as e:
            # Occurs if response is empty

            raise NotFoundError(
                'Ldap search "{0}" with filter {1} did not returned any result.',
                ldap_search_request.search_base,
                ldap_search_request.search_filter,
            ) from e

        return ldap_response
