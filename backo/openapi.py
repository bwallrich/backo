"""
Utility class to convert backo Collection to OpenAPI specification.
"""

from typing import Any


# TODO refactor this ugly implementation
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
        if route not in self.__routes:
            self.__routes[route] = {}

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

        self.__routes[route]["get"] = spec

    def add_post_item(
        self,
        route: str,
        item_name: str,
        item_schema: dict,
        ok: tuple[int, str],
        errors: list[tuple[int, str]],
    ) -> None:
        if route not in self.__routes:
            self.__routes[route] = {}

        spec: dict[str, Any] = {}
        spec["summary"] = f"Add an item in {item_name} collection."
        spec["operationId"] = f"add_{item_name}"

        required: list[str] = []
        properties: dict[str, Any] = {}
        file_properties: dict[str, Any] = {}
        base_properties: dict[str, Any] = {}
        for prop_name, scheme in item_schema["sub_scheme"].items():
            if prop_name == "_id":
                continue

            if scheme["required"]:
                required.append(prop_name)

            property = {}
            property["title"] = prop_name

            property["type"] = _convert_type(scheme["types"])
            if property["type"] == "file":
                property["type"] = "string"
                property["contentEncoding"] = "base64"

                file_properties[prop_name] = {
                    "title": prop_name,
                    "type": "string",
                    "format": "binary",
                }
            else:
                base_properties[prop_name] = property
            properties[prop_name] = property

        multipart_properties: dict[str, Any] = {
            "_json": {
                "type": "object",
                "required": required,
                "properties": base_properties,
            },
        }
        multipart_properties |= file_properties

        spec["requestBody"] = {"content": {}}
        spec["requestBody"]["content"] = {
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
                    "required": ["_json"],  # TODO required files ?
                    "properties": multipart_properties,
                },
                "encoding": {"_json": {"contentType": "application/json"}},
            },
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

        self.__routes[route]["post"] = spec

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

            properties[prop_name] = property

        self.__schemas[name] = {
            "title": name,
            "type": "object",
            "required": required,
            "properties": properties,
        }

    def get_schemas(self) -> dict:
        return self.__schemas
