import base64

from .connection import LdapSearchRequest


class MapDNToBase64ID:
    """DN based convertion between backo `_id`s and ldap search parameters."""

    def id(self, ldap_response):
        """Uses the URL safe base64 serialization of the DN as backo `_id`.

        :param ldap_response: An ldap3 response object. It is a dict in the form
        `{"dn": dn, "attributes": attributes}`, where `attributes` is a dict
        containing values of queried LDAP attributes.
        """
        return str(base64.urlsafe_b64encode(ldap_response[0]["dn"].encode()), "ascii")

    def search_request(self, _id):
        """Given the specified backo `_id`, must return ldap search parameters
        (search base + search filter) that is guaranteed to return the single
        entry corresponding to the `_id`, if it exists.

        :param _id: Backo `_id` of the LDAP item to search. It is assumed to
        have been generated using the id() method of this class.
        """

        # Decode the base64 encoded dn used as a search base
        # Default search filter
        return LdapSearchRequest(
            str(base64.urlsafe_b64decode(_id), "ascii"),
            "(objectClass=*)",
        )


class MapAttributeToID:
    """Use an LDAP attribute of an item as backo `_id`."""

    def __init__(self, search_base, attribute):
        """
        The item represented by a given `_id` is assumed to be retrieved from
        `search_base`, searching for the LDAP item with `_id` as `attribute`.

        For example, `search_base` might be `ou=groups,dc=example,dc=org` with
        `attribute` set to `gidNumber`.

        :param search_base: A static search base to initialize the LDAP search
        :param attribute: The attribute representing the ID
        """
        self.search_base = search_base
        self.attribute = attribute

    def id(self, ldap_response):
        """Returns the value of the LDAP attribute `self.attribute` as a backo `_id`.

        :param ldap_response: An ldap3 response object. It is a dict in the form
        `{"dn": dn, "attributes": attributes}`, where `attributes` is a dict
        containing values of queried LDAP attributes.
        """
        return ldap_response[0]["attributes"][self.attribute]

    def search_request(self, _id):
        """Builds an LdapSearch object that can be used to retrive the object
        whose `self.attribute` value is `_id` within the `search_base`.

        :param _id: Backo `_id` of the LDAP item to search. It is assumed to
        have been generated using the id() method of this class.
        """

        return LdapSearchRequest(
            self.search_base, f"({self.attribute}={_id})", [self.attribute]
        )


class RefAttributeSelfID:
    def ref_id(self, attribute):
        return attribute


class RefAttributeToBase64ID:
    def ref_id(self, attribute):
        return str(base64.urlsafe_b64encode(attribute.encode()), "ascii")


class Attribute:
    """Loads a JSON field from en LDAP attribute."""

    def __init__(self, ldap_attribute):
        """
        :param ldap_attribute: The LDAP attribute name to load data from.
        """
        self.ldap_attribute = ldap_attribute

    def load(self, root_ldap_response, _ldap_attribute_response):
        """
        Loads the value of ldap_attribute from the ldap_response and returns it
        as a value for the current JSON field.

        :param ldap_response: An ldap3 response object. It is a dict in the form
        `{"dn": dn, "attributes": attributes}`, where `attributes` is a dict
        containing values of queried LDAP attributes.
        """
        return root_ldap_response[0]["attributes"][self.ldap_attribute]

    def search_request(self, ldap_search: LdapSearchRequest):
        """
        Updates the specified LDAP search parameters to ensure the field can be
        loaded from the search response.

        The result of the LDAP search performed with those parameters will
        indeed be passed later to the load() method as the ldap_response, so
        ldap_response must contain the value of the ldap_attribute.

        To do so, the requested attribute is added to the list of `attributes`
        that should be returned by the search.

        :param ldap_search: An already initialized LdapSearch instance that
        should be completed so the search result includes the requested
        attribute
        """
        ldap_search.attributes.append(self.ldap_attribute)


class LdapRef:
    def __init__(self, attribute, reverse=RefAttributeSelfID()):
        self.attribute = attribute
        self.reverse = reverse

    def load(self, root_ldap_response, _attribute_ldap_response):
        return self.reverse.ref_id(root_ldap_response[0]["attributes"][self.attribute])

    def search_request(self, ldap_search: LdapSearchRequest):
        ldap_search.attributes.append(self.attribute)
