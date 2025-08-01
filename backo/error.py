"""Module providing Error management"""

from enum import Enum, auto

PREFIX = "MODEL_"


class ErrorType(Enum):
    """
    Specifics Errors for backo.
    Use a ErrorType value (for future internationalisation)
    """

    ALREADYEXIST = auto()
    READONLY = auto()
    NOTFOUND = auto()
    NOAPP = auto()
    COLLECTION_NOT_FOUND = auto()
    COLLECTION_NOT_REGISTERED = auto()
    FIELD_NOT_FOUND = auto()
    NOT_A_REF = auto()
    UNSET_SAVE = auto()
    RELOAD_UNSED = auto()
    REFSLIST_NOT_EMPTY = auto()
    NOT_IMPLEMENTED = auto()
    MONGO_CONNECT_ERROR = auto()
    SELECT_ERROR = auto()
    ACTION_NOT_AVAILABLE = auto()
    ACTION_FORBIDDEN = auto()
    UNAUTHORIZED = auto()
    NOT_DIR = auto()
    SELECTOR_NOT_FOUND = auto()
    DEVELOPPER = auto()
    RIGHT = auto()

    def __repr__(self):
        return PREFIX + self.name


class Error(TypeError):
    """
    A Error returned by objects
    (use to internalize error messages)
    """

    def __init__(self, codeError: str, message, variableName: str = None):
        """ """
        # Call the base class conDictor with the parameters it needs
        TypeError.__init__(self, message)

        self.error_code = codeError
        self.message = message
        self.variable_name = variableName

    def __str__(self):
        if self.variable_name:
            return f"{self.variable_name}: {self.message} ({self.error_code})"
        return f"{self.message} ({self.error_code})"
