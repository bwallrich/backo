"""
Utility class to convert backo Collection to OpenAPI specification.
"""

from backo.action import Action

from typing import Any


JSON_PATCH_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "oneOf": [
            {
                "additionalProperties": False,
                "required": ["value", "op", "path"],
                "properties": {
                    "path": {
                        "description": "A JSON Pointer path.",
                        "type": "string",
                    },
                    "op": {
                        "description": "The operation to perform.",
                        "type": "string",
                        "enum": ["add", "replace", "test"],
                    },
                    "value": {"description": "The value to add, replace or test."},
                },
            },
            {
                "additionalProperties": False,
                "required": ["op", "path"],
                "properties": {
                    "path": {
                        "description": "A JSON Pointer path.",
                        "type": "string",
                    },
                    "op": {
                        "description": "The operation to perform.",
                        "type": "string",
                        "enum": ["remove"],
                    },
                },
            },
            {
                "additionalProperties": False,
                "required": ["from", "op", "path"],
                "properties": {
                    "path": {
                        "description": "A JSON Pointer path.",
                        "type": "string",
                    },
                    "op": {
                        "description": "The operation to perform.",
                        "type": "string",
                        "enum": ["move", "copy"],
                    },
                },
            },
        ]
    },
}


def _convert_type(types: list[str]) -> str:
    """
    Convert stricto type to Openapi type
    """
    if "String" in types:
        return "string"
    elif "Int" in types:
        return "integer"
    elif "Float" in types:
        return "number"
    elif "Bool" in types:
        return "boolean"
    elif "List" in types:
        return "array"
    elif "File" in types:
        return "file"
    elif "Datetime" in types:
        return "date-time"
    elif "Dict" in types:
        return "object"
    raise ValueError(f"Could not convert {types} to OpenAPI type.")


class OpenAPISpec:
    def __init__(self):
        self.__routes: dict[str, dict] = {}
        self.__schemas: dict[str, dict] = {}

    def add_get_all(
        self,
        route: str,
        item_name: str,
        ok: tuple[int, str],
        errors: list[tuple[int, str]],
    ) -> None:
        spec: dict[str, Any] = {}
        spec["summary"] = (
            f"List all existing item in {item_name} collection, with eventual filtering."
        )
        spec["operationId"] = f"list_{item_name}"
        spec["parameters"] = [
            {
                "name": "qstring",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": "Query string",
            }
        ]
        spec["responses"] = {}
        spec["responses"][str(ok[0])] = {
            "description": ok[1],
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "result": {
                                "type": "array",
                                "items": {"$ref": f"#/components/schemas/{item_name}"},
                            },
                            "total": {"type": "integer"},
                            "_skip": {"type": "integer"},
                            "_page": {"type": "integer"},
                        },
                    }
                }
            },
        }

        for error_code, error_msg in errors:
            spec["responses"][str(error_code)] = {
                "description": error_msg,
                "content": {"text/plain": {}},
            }

        self.__add_spec(route, "get", spec)

    def add_post_item(
        self,
        route: str,
        item_name: str,
        item_schema: dict,
        ok: tuple[int, str],
        errors: list[tuple[int, str]],
    ) -> None:
        spec: dict[str, Any] = {}
        spec["summary"] = f"Add an item in {item_name} collection."
        spec["operationId"] = f"add_{item_name}"

        spec["requestBody"] = {
            "content": _extract_requestbody_content(item_schema["sub_scheme"])
        }

        spec["responses"] = {}
        spec["responses"][str(ok[0])] = {
            "description": ok[1],
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{item_name}"}
                }
            },
        }

        for error_code, error_msg in errors:
            spec["responses"][str(error_code)] = {
                "description": error_msg,
                "content": {"text/plain": {}},
            }

        self.__add_spec(route, "post", spec)

    def add_check_item(
        self,
        route: str,
        item_name: str,
        item_schema: dict[str, Any],
        code: tuple[int, str],
    ) -> None:
        spec: dict[str, Any] = {}
        spec["summary"] = f"Check if item can be put in {item_name} collection."
        spec["operationId"] = f"check_{item_name}"

        spec["requestBody"] = {
            "content": _extract_requestbody_content(item_schema["sub_scheme"])
        }

        spec["responses"] = {}
        spec["responses"][str(code[0])] = {
            "description": code[1],
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    }
                }
            },
        }

        self.__add_spec(route, "post", spec)

    def add_get_item(
        self,
        route: str,
        item_name: str,
        item_schema: dict[str, Any],
        ok: tuple[int, str],
        errors: list[tuple[int, str]],
    ):
        spec: dict[str, Any] = {}
        spec["summary"] = (
            f"Get the item identified by {{id}} in {item_name} collection."
        )
        spec["operationId"] = f"get_{item_name}"
        spec["parameters"] = [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "Id of the item to retrieve",
            },
            {
                "name": "qstring",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": "Query string",
            },
        ]

        spec["responses"] = {}
        spec["responses"][str(ok[0])] = {
            "description": ok[1],
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{item_name}"}
                }
            },
        }
        for error_code, error_msg in errors:
            spec["responses"][str(error_code)] = {
                "description": error_msg,
                "content": {"text/plain": {}},
            }

        self.__add_spec(route, "get", spec)

        spec: dict[str, Any] = {}
        spec["summary"] = (
            f"Get the file {{path}} of item identified by {{id}} in {item_name} collection."
        )
        spec["operationId"] = f"get_{item_name}_path"

        files: list[str] = []
        for prop_name, prop_scheme in item_schema["sub_scheme"].items():
            if "File" in prop_scheme["types"]:
                files.append(prop_name)

        spec["parameters"] = [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "Id of the item",
            },
            {
                "name": "path",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "enum": files},
                "description": "File of the item to retrieve",
            },
        ]

        spec["responses"] = {}
        spec["responses"][str(ok[0])] = {
            "description": ok[1],
            "content": {"application/octet-stream": {}},
        }
        for error_code, error_msg in errors:
            spec["responses"][str(error_code)] = {
                "description": error_msg,
                "content": {"text/plain": {}},
            }

        self.__add_spec(route + "/{path}", "get", spec)

    def add_put_item(
        self,
        route: str,
        item_name: str,
        item_schema: dict[str, Any],
        ok: tuple[int, str],
        errors: list[tuple[int, str]],
    ):
        spec: dict[str, Any] = {}
        spec["summary"] = (
            f"Modify the item identified by {{id}} in {item_name} collection."
        )
        spec["operationId"] = f"put_{item_name}"
        spec["parameters"] = [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "Id of the item to modify",
            },
        ]

        spec["requestBody"] = {
            "content": _extract_requestbody_content(item_schema["sub_scheme"])
        }

        spec["responses"] = {}
        spec["responses"][str(ok[0])] = {
            "description": ok[1],
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{item_name}"}
                }
            },
        }

        for error_code, error_msg in errors:
            spec["responses"][str(error_code)] = {
                "description": error_msg,
                "content": {"text/plain": {}},
            }

        self.__add_spec(route, "put", spec)

    def add_del_item(
        self,
        route: str,
        item_name: str,
        ok: tuple[int, str],
        errors: list[tuple[int, str]],
    ):
        spec: dict[str, Any] = {}
        spec["summary"] = (
            f"Delete the item identified by {{id}} in {item_name} collection."
        )
        spec["operationId"] = f"del_{item_name}"

        spec["parameters"] = [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "Id of the item to delete",
            },
        ]

        spec["responses"] = {}
        spec["responses"][str(ok[0])] = {
            "description": ok[1],
            "content": {"text/plain": {}},
        }

        for error_code, error_msg in errors:
            spec["responses"][str(error_code)] = {
                "description": error_msg,
                "content": {"text/plain": {}},
            }

        self.__add_spec(f"/{route}/{{id}}", "del", spec)

    def add_patch_item(
        self,
        route: str,
        item_name: str,
        ok: tuple[int, str],
        errors: list[tuple[int, str]],
    ):
        spec: dict[str, Any] = {}
        spec["summary"] = (
            f"Patch the item identified by {{id}} in {item_name} collection."
        )
        spec["operationId"] = f"patch_{item_name}"
        spec["parameters"] = [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "Id of the item to delete",
            },
        ]

        spec["requestBody"] = {
            "content": {},
            "description": "A json-patch object or an array of json-patch item for this item",
        }
        spec["requestBody"]["content"] = {
            "application/json": {
                "schema": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/json-patch"},
                        {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/json-patch"},
                        },
                    ]
                }
            }
        }
        spec["responses"] = {}
        spec["responses"][str(ok[0])] = {
            "description": ok[1],
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{item_name}"}
                }
            },
        }

        for error_code, error_msg in errors:
            spec["responses"][str(error_code)] = {
                "description": error_msg,
                "content": {"text/plain": {}},
            }

        self.__add_spec(route, "patch", spec)

    def add_actions(
        self,
        base_route: str,
        item_name: str,
        actions: dict[str, Action],
        ok: tuple[int, str],
        errors: list[tuple[int, str]],
    ):
        for name, action in actions.items():
            print(f"REGISTER {name}")
            spec: dict[str, Any] = {}
            spec["summary"] = (
                f"Trigger the action {name} on item identified by {{id}} in {item_name} collection."
            )
            spec["operationId"] = f"action_{name}_on_{item_name}"
            spec["parameters"] = [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Id of the item on which trigger the action",
                },
            ]

            spec["requestBody"] = {
                "content": _extract_requestbody_content(
                    action.get_schema()["sub_scheme"]
                )
            }

            spec["responses"] = {}
            spec["responses"][str(ok[0])] = {
                "description": ok[1],
                "content": {},
            }

            for error_code, error_msg in errors:
                spec["responses"][str(error_code)] = {
                    "description": error_msg,
                    "content": {"text/plain": {}},
                }

            self.__add_spec(base_route + f"/{name}/{{id}}", "post", spec)

    def __add_spec(self, route: str, method: str, spec: dict) -> None:
        if route not in self.__routes:
            self.__routes[route] = {}

        self.__routes[route][method] = spec

    def get_routes(self) -> dict:
        return self.__routes

    def add_schema(self, name: str, item_schema: dict) -> None:
        required: list[str] = []
        properties: dict[str, Any] = {}
        for prop_name, scheme in item_schema["sub_scheme"].items():
            property = {"title": prop_name}
            if scheme["required"]:
                required.append(prop_name)

            property["type"] = _convert_type(scheme["types"])
            # missing "items" . "type" for array
            if property["type"] == "object":
                self.add_schema(f"{name}_{prop_name}", scheme)
                property["$ref"] = f"#/components/schemas/{name}_{prop_name}"
            elif property["type"] == "file":
                property["type"] = "string"
                property["contentEncoding"] = "base64"
            elif property["type"] == "date-time":
                property["type"] = "string"
                property["format"] = "date-time"

            properties[prop_name] = property

        self.__schemas[name] = {
            "title": name,
            "type": "object",
            "required": required,
            "properties": properties,
        }

    def get_schemas(self) -> dict:
        return self.__schemas


def _extract_requestbody_content(sub_scheme: dict[str, Any]):
    required: list[str] = []
    file_required: list[str] = []
    properties: dict[str, Any] = {}
    file_properties: dict[str, Any] = {}
    base_properties: dict[str, Any] = {}
    for prop_name, scheme in sub_scheme.items():
        if prop_name == "_id":
            continue

        if scheme["rights"]["modify"] is not None and not scheme["rights"]["modify"]:
            continue

        if scheme["required"]:
            required.append(prop_name)

        property = {}
        property["title"] = prop_name

        property["type"] = _convert_type(scheme["types"])
        if property["type"] == "file":
            property["type"] = "string"
            property["contentEncoding"] = "base64"
            if scheme["required"]:
                file_required.append(prop_name)

            file_properties[prop_name] = {
                "title": prop_name,
                "type": "string",
                "format": "binary",
            }
        elif property["type"] == "date-time":
            property["type"] = "string"
            property["format"] = "date-time"
        else:
            base_properties[prop_name] = property

        if prop_name != "_meta":
            properties[prop_name] = property

    multipart_properties: dict[str, Any] = {
        "_json": {
            "type": "object",
            "required": required,
            "properties": base_properties,
        },
    }
    multipart_properties |= file_properties

    return {
        "application/json": {
            "schema": {
                "type": "object",
                "required": required,
                "properties": properties,
            }
        },
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "required": ["_json"] + file_required,
                "properties": multipart_properties,
            },
            "encoding": {"_json": {"contentType": "application/json"}},
        },
    }
