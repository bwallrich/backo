"""
The decortators used for flask routes
"""

# pylint: disable=logging-fstring-interpolation

import sys
import logging
import traceback
from functools import wraps
from flask import request

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
from .error import Error as BackError, ErrorType as BackoErrorType
from .log import log_system

log = log_system.get_or_create_logger("http", logging.ERROR)


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
        except BackError as e:
            log.error(f"{e.error_code}: {e.message}")
            log.error(traceback.print_exc())
            if e.error_code == BackoErrorType.UNAUTHORIZED:
                return return_http_error(403, e.message)
            if e.error_code == BackoErrorType.NOTFOUND:
                return return_http_error(404, e.message)
            if e.error_code == BackoErrorType.ACTION_NOT_AVAILABLE:
                return return_http_error(424, e.message)
            if e.error_code == BackoErrorType.ACTION_FORBIDDEN:
                return return_http_error(403, e.message)
            if e.error_code == BackoErrorType.FIELD_NOT_FOUND:
                return return_http_error(400, e.message)
            # default error
            return return_http_error(500, e.message)
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
            log.error(repr(e))
            log.error(traceback.print_exc())
            return return_http_error(400, repr(e))
        except AttributeError as e:
            log.error(f" Error AttributeError {str(e)}")
            log.error(traceback.print_exc())
            return return_http_error(400, str(e))
        except TypeError as e:
            log.error(f" Error TypeError {str(e)}")
            log.error(traceback.print_exc())
            return return_http_error(400, str(e))
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error(f" Error Exception {str(e)}")
            log.error(traceback.print_exc())
            return return_http_error(500, str(e))

    return wrapper


# def check_method(methods: list):
#     """
#     check if the method is in a list of methods [ 'GET', 'POST' ]
#     """
#
#     def inner(f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             if request.method not in methods:
#                 return return_http_error(405, "Method not Allowed")
#             return f(*args, **kwargs)
#
#         return wrapper
#
#     return inner


# def check_query_parameters(available_params: list):
#     """
#     check if the method is in a list of methods [ 'GET', 'POST' ]
#     """
#
#     def inner(f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             query = request.args
#             for param_name in query.keys():
#                 if param_name not in available_params:
#                     return return_http_error(
#                         406,
#                         f'Not acceptable : query  parameter "{param_name}" not allowed.',
#                     )
#             return f(*args, **kwargs)
#
#         return wrapper
#
#     return inner
