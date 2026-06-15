from dataclasses import dataclass, field


@dataclass
class LdapSearchRequest:
    """A dataclass to store parameters that can be passed to the ldap
    connection.search() method.
    """

    search_base: str = ""
    search_filter: str = "(objectClass=*)"
    attributes: list[str] = field(default_factory=list)
