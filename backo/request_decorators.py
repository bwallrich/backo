"""
The decortators used for flask routes
"""

from functools import wraps
from flask import request


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


def check_method(methods: list):
    """
    check if the method is in a list of methods [ 'GET', 'POST' ]
    """

    def inner(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method not in methods:
                return return_http_error(405, "Method not Allowed")
            return f(*args, **kwargs)

        return wrapper

    return inner


def check_query_parameters(available_params: list):
    """
    check if the method is in a list of methods [ 'GET', 'POST' ]
    """

    def inner(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            query = request.args
            for param_name in query.keys():
                if param_name not in available_params:
                    return return_http_error(
                        406,
                        f'Not acceptable : query  parameter "{param_name}" not allowed.',
                    )
            return f(*args, **kwargs)

        return wrapper

    return inner
