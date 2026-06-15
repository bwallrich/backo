import unittest

from hamcrest import (
    assert_that,
    contains_exactly,
    has_entries,
    contains_inanyorder,
)

from backo.database.item import DatabaseItem

from backo.ldap.item import (
    MapDNToBase64ID,
    MapAttributeToID,
    Attribute,
    LdapRef,
    RefAttributeToBase64ID,
)


class TestLdapItem(unittest.TestCase):
    def test_load_attribute(self):
        """Tests LdapItem.load method for a simple item, without references.

        The item must be loaded from the mocked LDAP response.
        """

        id_mapper = MapDNToBase64ID()
        ldap_item = DatabaseItem(
            id_mapper,
            {
                "login": Attribute("uid"),
                "name": Attribute("name"),
                "contact": Attribute("mail"),
            },
        )

        dn = "uid=jdoe,ou=people,dc=example,dc=org"

        # Real call to the method under test
        item = ldap_item.load(
            [
                {
                    "dn": dn,
                    "attributes": {
                        # Single values
                        "uid": "jdoe",
                        "uidNumber": 12,
                        "name": "John Doe",
                        # A true multiple value
                        "mail": ["mail1@example.org", "mail2@jdoe.fr"],
                    },
                }
            ],
            {
                "login": None,
                "name": None,
                "contact": None,
            },
        )

        assert_that(
            item,
            has_entries(
                {
                    "login": "jdoe",
                    "name": "John Doe",
                    "contact": contains_exactly("mail1@example.org", "mail2@jdoe.fr"),
                }
            ),
        )

    def test_load_simple_ref(self):
        """Tests LdapItem.load method for a simple item, without references.

        The item must be loaded from the mocked LDAP response.
        """

        id_mapper = MapDNToBase64ID()
        ldap_item = DatabaseItem(
            id_mapper,
            {
                # No reverse is specified in the LdapRef specification, so it is
                # assumed that the value itself is alread a backo _id. It does
                # not need to be transformed.
                "primary_group": LdapRef(attribute="gidNumber")
            },
        )

        dn = "uid=jdoe,ou=people,dc=example,dc=org"

        # Real call to the method under test
        item = ldap_item.load(
            [
                {
                    "dn": dn,
                    "attributes": {
                        "gidNumber": 1312,
                    },
                }
            ],
            {"primary_group": None},
        )

        assert_that(
            item,
            has_entries(
                {
                    "primary_group": 1312,
                }
            ),
        )

        assert_that(item.keys(), contains_exactly("primary_group"))

    def test_load_dn_ref(self):
        """Tests LdapItem.load method for a simple item, without references.

        The item must be loaded from the mocked LDAP response.
        """

        # Example id mapper used by the LdapItem
        group_id_mapper = MapAttributeToID("ou=groups,dc=example,dc=org", "gidNumber")

        # Id mapper used by the superadmin reference

        ldap_group_item = DatabaseItem(
            group_id_mapper,
            {
                # Backo field
                "superadmin": LdapRef(
                    # LDAP attribute
                    attribute="owner",
                    # The owner attribute is a DN that must be converted to a
                    # valid backo _id
                    reverse=RefAttributeToBase64ID(),
                )
            },
        )

        dn = "uid=jdoe,ou=people,dc=example,dc=org"

        # Real call to the method under test
        item = ldap_group_item.load(
            [
                {
                    "dn": dn,
                    "attributes": {
                        "owner": "uid=jdoe,ou=people,dc=example,dc=org",
                    },
                }
            ],
            {"superadmin": None},
        )

        assert_that(
            item,
            has_entries(
                {
                    "superadmin": RefAttributeToBase64ID().ref_id(
                        "uid=jdoe,ou=people,dc=example,dc=org"
                    ),
                }
            ),
        )
