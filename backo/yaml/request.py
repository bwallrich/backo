from typing import Any
from dataclasses import dataclass


@dataclass
class YamlSearchRequest:
    path: list[str|int]


@dataclass
class YamlSearchResponse:
    # TODO: support exclude path. It can be safely removed from value even in a
    # base response, because if an attribute needs it, it will still be included
    # in its attribute response.
    path: list[str|int]
    value: Any


@dataclass
class YamlCreateRequest:
    # TODO: support exclude path. Do not remove values from value as they might
    # be needed to init item, but ignore them only when the request is executed.
    # -> it's ok if the attributes removes it once it is done with it
    path: list[str|int]
    value: Any
    created_id: str|None = None


@dataclass
class YamlCreateResponse:
    created_id: str


@dataclass
class YamlDeleteRequest:
    path: list[str|int]


@dataclass
class YamlDeleteResponse:
    pass


@dataclass
class YamlUpdateRequest:
    path: list[str|int]
    value: Any


@dataclass
class YamlUpdateResponse:
    pass
