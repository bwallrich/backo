"""
Utility class to convert backo Collection to OpenAPI specification.
"""

from typing import Any


def _convert_type(types: list[str]) -> str:
    """
    Convert stricto type to Openapi type
    """
    if "String" in types:
        return "string"
    elif "Integer" in types:
        return "integer"
    elif "Float" in types:
        return "number"
    elif "Bool" in types:
        return "boolean"
    elif "Dict" in types:
        return "object"
    elif "List" in types:
        return "array"
    raise ValueError(f"Could not convert {types} to OpenAPI type.")


class OpenAPISpec:
    def __init__(self):
        self.__routes: dict[str, dict] = {}
        self.__schemas: dict[str, dict] = {}

    def add_get_all(
        self,
        item_name: str,
        route: str,
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

    def add_post_item(self) -> None:
        pass

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

            if property["type"] == "object":
                self.add_schema(f"{name}_{prop_name}", scheme)
                property["$ref"] = f"#/components/schemas/{name}_{prop_name}"

            properties[prop_name] = property

        self.__schemas[name] = {
            "title": name,
            "type": "object",
            "required": required,
            "properties": properties,
        }

    def get_schemas(self) -> dict:
        return self.__schemas
