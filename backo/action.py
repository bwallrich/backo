"""
Module providing the action
"""
# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

import sys

from datetime import datetime
from .current_user import current_user
from .log import log_system
from .error import Error, ErrorType

log = log_system.get_or_create_logger("Action")

sys.path.insert(1, "../../stricto")
from stricto import Dict, Int, String


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
        execute = kwargs.pop('can_execute', kwargs.pop('exec', True))
        availability = kwargs.pop('availability', kwargs.pop('doable', True))
        self.on_trig = on_trig
        Dict.__init__(self, schema, **kwargs)
        self._params['execute'] = execute
        self._params['availability'] = availability


    def check_params(self, param_name, o):
        """
        Check if can execute the action
        """
        p = self._params.get(param_name, False)
        if not callable(p):
            return bool(p)
        return bool(p( self.app, self.collection, self, o))

    def can_execute( self, o):
        """
        Check if can execute the action
        """
        return self.check_params( 'execute', o)

    def is_available( self, o):
        """
        Check if this action is doable
        """
        return self.check_params( 'availability', o)

    def go(self, o):
        """
        Launch the action
        
        o is the object (if exists)
        """

        if not self.is_available(o):
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
        return self.on_trig( self.app, self.collection, self, o )
