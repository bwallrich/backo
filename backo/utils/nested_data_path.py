"""Defines utility methods that can be used to work on a nested list/dict data
structure using paths.

All dicts use strings as keys.

The data structure can be a list or a dict with an other valid data structure as
values, or any arbitrary python type that is not a list or a dict.

For example:
```python
[
    Item(),
    10,
    {
        "nested":
            "data": ["bip", "boop", Item(2)]
    }
]
```

Paths are lists of strings and list indexes that reference an item in the data
structure. For example, `[2, "nested", "data", 1]` refers to "boop" in the
previous example.

A path does not need to reach a leaf in the structure, so `[2, "nested"]` is a
valid path to `"data": ["bip", "boop", Item(2)]`.
"""

class PathError(Exception):
    """Error raised if a path could not be processed.
    """

    def __init__(self, data, path):
        """Initializes the standard exception with an excplicit message.
        """
        super().__init__(f"Path {path} could not be resolved in {data}.")


def find(data, path):
    """Returns the item at path in data.

    Raises a PathError if the path cannot reach a valid node in data.

    :param data: a nested list/dict data structure
    :param path: a list of string keys and list indexes
    :return: the value at path in data
    """
    if len(path) > 0:
        if isinstance(data, dict):
            return find(data[path[0]], path[1:])
        if isinstance(data, list):
            if isinstance(path[0], int):
                return find(data[path[0]], path[1:])
            # The path item must be a list index
            raise PathError(data, path)
        # The path item must be a string key
        raise PathError(data, path)
    return data

def _update_next_dict(data, path, value):
    try:
        update(data[path[0]], path[1:], value)
    except KeyError:
        if isinstance(path[1], str):
            data[path[0]] = {}
        elif isinstance(path[1], int):
            data[path[0]] = []
        update(data[path[0]], path[1:], value)

def _update_next_list(data, path, value):
    if isinstance(path[0], int):
        try:
            update(data[path[0]], path[1:], value)
        except IndexError:
            data[-1 : path[0]] = [None] * (path[0] - len(data))
            if isinstance(path[1], str):
                data.append({})
            elif isinstance(path[1], int):
                data.append([])
            update(data[path[0]], path[1:], value)
    else:
        # List index must be int
        raise PathError(data, path)

def update(data, path, value):
    """Updates the item at path in data with the associated value, so that the
    next call to search(data, path) will return value.

    This means the udpate method attempts to create the path within the data if
    it does not exist, and raises a PathError if the path could not be built.

    The update process navigates the data structure as the find method does.

    If at some point the referenced item does not exist, it is created as
    follows:
    - if the current path item is a string key, assign the next value to that
      key in the current data item that must be a dict. If it's not, a PathError
      is raised.
    - if the current path item is a list index, insert the next value at this
      index in the current data item that must be a list. If it's not, a
      PathError is raised. If the list is too short, None values are inserted up
      to the requested list index.
    The next value is the value specified as parameter if the current path item
    is the last element of the path, else its a dict or list recursively created
    according to the previous process according to the type of the next item in
    the path: if its a string key, a new dict is created, if its a list index, a
    new list is created.

    :param data: a nested list/dict data structure
    :param path: a list of string keys and list indexes
    :param value: the value to assign. Can be anything.
    """
    if len(path) > 1:
        if isinstance(data, dict):
            _update_next_dict(data, path, value)
        elif isinstance(data, list):
            _update_next_list(data, path, value)
        else:
            raise PathError(data, path)
    elif len(path) == 1:
        if isinstance(data, dict):
            data[path[0]] = value
        elif isinstance(data, list) and isinstance(path[0], int):
            try:
                data[path[0]] = value
            except IndexError:
                data[-1 : path[0]] = [None] * (path[0] - len(data))
                data.append(value)
        else:
            raise PathError(data, path)
    else:
        data = value


def delete(data, path):
    """Deletes the item at path in data, so that the next call to find(data,
    path) will raise a PathError.

    The delete process navigates the data structure as the find method does.

    The item referenced at path is deleted using the python `del` statement. If
    the last element of the path is a key, it is removed from the dict that
    contains it. If it's a list index, it is popped from the list that contains
    it.

    Raises a PathError if the path cannot reach a valid node in data.

    :param data: a nested list/dict data structure
    :param path: a list of string keys and list indexes
    """
    if len(path) > 1:
        if isinstance(data, dict):
            delete(data[path[0]], path[1:])
        elif isinstance(data, list) and isinstance(path[0], int):
            delete(data[path[0]], path[1:])
        else:
            raise PathError(data, path)
    elif len(path) == 1:
        if isinstance(data, dict):
            del data[path[0]]
        elif isinstance(data, list) and isinstance(path[0], int):
            del data[path[0]]
        else:
            raise PathError(data, path)
    else:
        del data
