"""Module providing Error management"""

import sys

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import StrictoError


class DBError(Exception, StrictoError):
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


class FileError(Exception, StrictoError):
    """
    Extented :py:class:`StrictoError` with ``Error``
    Used by file_connectors  for all errors related to files
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


class NotFoundError(Exception, StrictoError):
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


class PathNotFoundError(Exception, StrictoError):
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


class BackoError(Exception, StrictoError):
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


class SessionError(Exception, StrictoError):
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
