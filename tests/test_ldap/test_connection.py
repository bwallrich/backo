import unittest
from unittest.mock import patch

from hamcrest import (
    assert_that,
    contains_exactly,
    has_properties,
    has_entries,
)

from backo.ldap.connection import LdapConnection


@patch("ldap3.Connection", autospec=True)
class TestLdapConnection(unittest.TestCase):

    @patch("backo.ldap.request.LdapSearchRequest", autospec=True)
    def test_search(self, ldap_search_request, ldap_connection):
        """Tests LdapSearchEngine.search method for an existing item.

        The returned item must correspond to the item loaded by the ldap_item
        from the connection.search results.
        """

        connection = LdapConnection(ldap_connection.return_value)

        mock_dn = "uid=jdoe,ou=people,dc=example,dc=org"

        ## Mock everything for conn.search to work as expected

        def mock_attributes():
            return {
                # Single values
                "uid": "jdoe",
                "uidNumber": 12,
                "name": "John Doe",
                # A true multiple value
                "mail": ["mail1@example.org", "mail2@jdoe.fr"],
            }

        # The mock_search side_effect always return a good value, because we
        # don't want to make assertions in mocking. It will be asserted later
        # that conn.search was called with valid parameters.
        def mock_search(_search_base, _search_filter, attributes):
            response = [{"dn": mock_dn, "attributes": mock_attributes()}]

            if isinstance(attributes, list):
                attributes_to_remove = set(mock_attributes().keys()) - set(attributes)
                for attribute in attributes_to_remove:
                    del response[0]["attributes"][attribute]
            ldap_connection.return_value.response = response
            return response

        ldap_connection.return_value.search.side_effect = mock_search

        # Real call to the method under test
        response = connection.execute_search(ldap_search_request.return_value)

        # Ensure search was called with appropriate parameters.
        assert_that(
            ldap_connection.return_value.search.call_args_list,
            contains_exactly(
                has_properties(
                    args=contains_exactly(
                        ldap_search_request.return_value.search_base,
                        ldap_search_request.return_value.search_filter,
                    ),
                    kwargs=has_entries(
                        attributes=ldap_search_request.return_value.attributes
                    ),
                )
            ),
        )

        assert_that(
            response,
            contains_exactly(
                has_entries(
                    {"dn": mock_dn, "attributes": has_entries(mock_attributes())}
                )
            ),
        )
