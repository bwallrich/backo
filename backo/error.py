"""Module providing Error management"""
import sys
from enum import Enum, auto

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import StrictoError


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


class DBError(Error, StrictoError):
    """
    Extented :py:class:`StrictoError` with ``Error``
    Used by connectors for all errors related to DB and Storage
    """

    def __init__(self, message: str, *args: object, **kwargs: object):
        """
        init with all params
        """
        StrictoError.__init__(self, message, *args, **kwargs)
        super().__init__(message, *args)

    def __repr__(self):
        return f'{self.__class__.__bases__[0].__name__}("{self.to_string()}")'

    def __str__(self):
        return repr(self)
    
class NotFoundError(Error, StrictoError):
    """
    Extented :py:class:`StrictoError` with ``Error``
    Used to say "not found"
    """

    def __init__(self, message: str, *args: object, **kwargs: object):
        """
        init with all params
        """
        StrictoError.__init__(self, message, *args, **kwargs)
        super().__init__(message, *args)

    def __repr__(self):
        return f'{self.__class__.__bases__[0].__name__}("{self.to_string()}")'

    def __str__(self):
        return repr(self)
    

class PathNotFoundError(Error, StrictoError):
    """
    Extented :py:class:`StrictoError` with ``Error``
    Used to say "the path/field is not found"
    """

    def __init__(self, message: str, *args: object, **kwargs: object):
        """
        init with all params
        """
        StrictoError.__init__(self, message, *args, **kwargs)
        super().__init__(message, *args)

    def __repr__(self):
        return f'{self.__class__.__bases__[0].__name__}("{self.to_string()}")'

    def __str__(self):
        return repr(self)
    
class BackoError(Error, StrictoError):
    """
    Extented :py:class:`StrictoError` with ``Error``
    Used to any ORM Errors
    """

    def __init__(self, message: str, *args: object, **kwargs: object):
        """
        init with all params
        """
        StrictoError.__init__(self, message, *args, **kwargs)
        super().__init__(message, *args)

    def __repr__(self):
        return f'{self.__class__.__bases__[0].__name__}("{self.to_string()}")'

    def __str__(self):
        return repr(self)
    
class SessionError(Error, StrictoError):
    """
    Extented :py:class:`StrictoError` with ``Error``
    Used to any Session / request Errors
    """

    def __init__(self, message: str, *args: object, **kwargs: object):
        """
        init with all params
        """
        StrictoError.__init__(self, message, *args, **kwargs)
        super().__init__(message, *args)

    def __repr__(self):
        return f'{self.__class__.__bases__[0].__name__}("{self.to_string()}")'

    def __str__(self):
        return repr(self)