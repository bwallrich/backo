"""
Module providing the Patch() Class
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys
import re

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import Dict, String


def must(value, o) -> bool:  # pylint: disable=unused-argument
    """check if start with a $.

    :param value: _description_
    :type value: _type_
    :param o: Not used
    :type o: _tyAnype_
    :return: True if start with a $.
    :rtype: bool
    """
    return bool(re.match(r"^\$.*", value))


class Patch(Dict):  # pylint: disable=too-few-public-methods
    """
    A Object for patching
    """

    def __init__(self):
        """
        available arguments
        """
        Dict.__init__(
            self,
            {
                "op": String(require=True, union=["test", "replace", "remove", "add"]),
                "path": String(
                    require=True,
                    # constraint=lambda value, o: bool(re.match(r"^\$.*", value)),
                    constraint=must,
                ),
                "value": String(),
            },
        )
