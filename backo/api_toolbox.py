"""
The toolbox for api
A set of functions
"""

import re
from werkzeug.datastructures import ImmutableMultiDict


def _append_to_filter(filter_as_dict: dict, key, value: list):
    """
    adding key to dict with transformation to int or float if we can
    """

    # Transform string to int or float
    typed_value = []
    for v in value:
        try:
            vv = int(v)
        except ValueError:
            try:
                vv = float(v)
            except ValueError:
                vv = v
        typed_value.append(vv)

    val = typed_value[0] if len(typed_value) == 1 else typed_value

    match = re.search(r"^([^\.]+)\.(.*)", key)
    if not match:
        filter_as_dict[key] = val
        return

    # a toto.$gt (with an operator)
    if re.findall(r"^\$", match.group(2)):
        filter_as_dict[match.group(1)] = (match.group(2), val)
        return

    sub = filter_as_dict.get(match.group(1), {})
    if not isinstance(sub, dict):
        sub = {}

    _append_to_filter(sub, match.group(2), value)
    filter_as_dict[match.group(1)] = sub


def multidict_to_filter(md: ImmutableMultiDict):
    """
    Transform a multi dict to filter (query string are immutable dict)

    see match in stricto for definition of a filter
    see https://tedboy.github.io/flask/generated/generated/werkzeug.ImmutableMultiDict.html


    [ ('toto', 'miam'), ('titi.tutu', '23.2') ('tata.$gt', 11)] ->
    {
        'toto' : "miam",
        'titi' : {
            'tutu' : 23.2
        },
        'tata' : ( '$gt', 11 )
    }
    """

    filter_as_dict = {}
    for key in md.keys():

        # ignoring keys starting with _
        if re.match(r"^_.*", key):
            continue

        value = md.getlist(key)
        _append_to_filter(filter_as_dict, key, value)

    return filter_as_dict
