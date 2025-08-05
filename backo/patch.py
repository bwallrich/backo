"""
Module providing the Item() Class
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys
import re


sys.path.insert(1, "../../stricto")
from stricto import Dict, String


class Patch(Dict):  # pylint: disable=too-many-instance-attributes
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
                    constraint=lambda value, o: bool(re.match(r"^\$.*", value)),
                ),
                "value": String(),
            },
        )
