"""
The toolbox for api
A set of functions
"""

import re
import json
from typing import Any
from flask import Request
from werkzeug.datastructures import ImmutableMultiDict


def flatter(out: dict, src: Any, root_path=[]) -> None:
    """avoid nested dict by combination of key.
    follow nested dict into list too.

    transform

    { 'location' : {
        'street' : 'far'
        }
    }

    into

    { 'location.street' : 'far' }



    :param out: the flattened dict
    :type out: dict
    :param src: the dict to "flatten"
    :type src: dict
    :param root_path: internal, defaults to []
    :type root_path: list, optional
    """
    if isinstance(src, dict):
        for key, value in src.items():
            flatter(out, value, root_path + [key])
        return

    if isinstance(src, list):
        a = []
        for value in src:
            if isinstance(value, dict):
                o = {}
                flatter(o, value)
                a.append(o)
            else:
                a.append(value)
        out[f'{".".join(root_path)}'] = a
        return

    out[f'{".".join(root_path)}'] = src


def unflatter(out: dict, path: list[str], value: Any) -> None:
    """unflatter dict

    This is the opposite of flatter()

    :param out: the output dict
    :type out: dict
    :param path: the key as a path, like [ 'location', 'street' ]
    :type path: list[str]
    :param value: any value
    :type value: Any
    """

    k = path.pop(0)
    if len(path) == 0:
        if isinstance(value, list):
            a = []
            for subv in value:
                if isinstance(subv, dict):
                    o = {}
                    for k, v in subv.items():
                        unflatter(o, k.split("."), v)
                    a.append(o)
                else:
                    a.append(subv)
            out[k] = a
        else:
            out[k] = value
        return
    out[k] = {}
    unflatter(out[k], path, value)


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
        if re.match(r"^_", key):
            continue

        value = md.getlist(key)
        append_path_to_filter(filter_as_dict, key, value)

    return filter_as_dict


def request_to_object(request: Request) -> Any:
    """Read the request and transform it to a struct

    :param request: The request given
    :type request: Request
    """

    # Json, return just the json
    if request.content_type == "application/json":
        return request.json

    if re.match(r"^multipart/form-data;", request.content_type):
        obj = {}
        if "_json" in request.form:
            obj = json.loads(request.form.get("_json"))

        # Adding other keys
        for key in request.form:
            value = request.form[key]
            # ignoring keys starting with _
            if re.match(r"^_", key):
                continue

            append_path_to_filter(obj, key, value)

        # Append files to the json struct
        for vpath in request.files:
            file = request.files[vpath]
            append_path_to_filter(obj, vpath, file)

        return obj

    return None
