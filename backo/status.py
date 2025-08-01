"""
Module providing the StatusType() Class
"""

from enum import Enum, auto


class StatusType(Enum):
    """
    Specifics status for this object
    """

    UNSET = auto()
    SAVED = auto()
    UNSAVED = auto()

    def __repr__(self):
        return self.name
