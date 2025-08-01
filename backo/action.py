"""
Module providing the action
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init


import sys

sys.path.insert(1, "../../stricto")
from stricto import Dict

from .log import log_system
from .error import Error, ErrorType
from .item import Item

log = log_system.get_or_create_logger("action")


class Action(Dict):  # pylint: disable=too-many-instance-attributes
    """
    An action
    """

    def __init__(self, schema: dict, on_trig, **kwargs):
        """
        available arguments
        """
        self.app = None
        self.name = None
        self.collection = None
        self.on_trig = on_trig

        # Add default right
        if "can_execute" not in kwargs:
            kwargs["can_execute"] = True
        if "can_see" not in kwargs:
            kwargs["can_see"] = True
        kwargs["can_read"] = True
        kwargs["can_modify"] = True
        kwargs["exists"] = True

        Dict.__init__(self, schema, **kwargs)

    def check_params(self, param_name, o: Item) -> bool:
        """
        Check if can execute the action
        """
        p = self._params.get(param_name, False)
        if not callable(p):
            return bool(p)
        return bool(p(self.app, self.collection, self, o))

    def can_see(self, o: Item) -> bool:
        """
        Check if this action exists for running
        """
        return self._rights.has_right("see", self, o)

    def can_execute(self, o: Item) -> bool:
        """
        Check if can execute the action
        object can be a Dict, a array of Dict, or None, depends ont the target for this actopn
        """
        return self._rights.has_right("execute", self, o)

    def go(self, o: Item) -> None:
        """
        Launch the action

        objeoct is the object (if exists)
        """

        if not self.can_see(o):
            log.error("Try to launch non available action %r", self.name)
            raise Error(
                ErrorType.ACTION_NOT_AVAILABLE,
                f"action {self.name} not available",
            )

        if not self.can_execute(o):
            log.error("Try to execute forbidden action %r", self.name)
            raise Error(
                ErrorType.ACTION_FORBIDDEN,
                f"action {self.name} forbidden",
            )

        log.debug("Execute action %r", self.name)
        return self.on_trig(self, o)
