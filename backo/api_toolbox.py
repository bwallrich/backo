"""
The toolbox for api
A set of functions
"""

import re
from werkzeug.datastructures import ImmutableMultiDict


def append_path_to_filter(filter_as_dict: dict, key, value: list | tuple):
    """transform a

    :param filter_as_dict: _description_
    :type filter_as_dict: dict
    :param key: _description_
    :type key: _type_
    :param value: _description_
    :type value: list | tuple
    """
    changed_value = value
    if isinstance(value, list):
        # Transform string to int or float if we can
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

        if len(typed_value) == 1:
            changed_value = typed_value[0]
        elif (
            len(typed_value) == 2
            and isinstance(typed_value[0], str)
            and re.findall(r"^\$", typed_value[0])
        ):
            changed_value = (typed_value[0], typed_value[1])
        else:
            changed_value = typed_value

    match = re.search(r"^([^\.]+)\.(.*)", key)
    if not match:
        filter_as_dict[key] = changed_value
        return

    # a toto.$gt (with an operator)
    if re.findall(r"^\$", match.group(2)):
        filter_as_dict[match.group(1)] = (match.group(2), changed_value)
        return

    sub = filter_as_dict.get(match.group(1), {})
    if not isinstance(sub, dict):
        sub = {}

    append_path_to_filter(sub, match.group(2), value)
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
        append_path_to_filter(filter_as_dict, key, value)

    return filter_as_dict
