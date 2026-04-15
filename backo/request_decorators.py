"""
The decortators used for flask routes
"""

# pylint: disable=logging-fstring-interpolation

import sys
import traceback
from functools import wraps
from flask import request

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import (
    SAttributeError,
    SError,
    STypeError,
    SSyntaxError,
    SConstraintError,
    SKeyError,
    SRightError,
)
from .error import NotFoundError, PathNotFoundError
from .log import log_system, LogLevel

log = log_system.get_or_create_logger("http", LogLevel.ERROR)


def return_http_error(code, message):
    """
    response a error code and message to the client
    """
    return message, code


def check_json(f):
    """
    Check if the data is json otherwise error
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.content_type != "application/json":
            return return_http_error(415, "Unsuported Media Type")
        return f(*args, **kwargs)

    return wrapper


def error_to_http_handler(f):
    """
    return a http message depends on the error raised
    """

    @wraps(f)
    def wrapper(*args, **kwargs):  # pylint: disable=too-many-return-statements
        try:
            return f(*args, **kwargs)
        except NotFoundError as e:
            return return_http_error(404, repr(e))
        except PathNotFoundError as e:
            return return_http_error(400, repr(e))
        except SRightError as e:
            log.error(repr(e))
            return return_http_error(403, repr(e))
        except (
            SAttributeError,
            STypeError,
            SSyntaxError,
            SConstraintError,
            SKeyError,
            SError,
        ) as e:
            log.error(str(e))
            log.error(traceback.format_exc())
            return return_http_error(400, str(e))
        except AttributeError as e:
            log.error(repr(e))
            log.error(traceback.format_exc())
            return return_http_error(400, str(e))
        except TypeError as e:
            log.error(str(e))
            log.error(traceback.format_exc())
            return return_http_error(400, str(e))
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error(str(e))
            log.error(traceback.format_exc())
            return return_http_error(500, str(e))

    return wrapper
