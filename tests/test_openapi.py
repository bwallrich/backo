"""
Test for OpenAPI specification generation.
"""

import unittest

from flask import Flask

from backo import (
    Backoffice,
    BlobFile,
    Bool,
    Collection,
    DBYmlConnector,
    Float,
    Int,
    Item,
    String,
)
from backo.action import Action
from backo.selection import Selection

YML_DIR = "/tmp/backo_tests_openapi"


class TestOpenAPI(unittest.TestCase):
    """
    Test OpenAPI specification generation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup test DBYmlConnector and clean it before each test
        self.__connector = DBYmlConnector(path=YML_DIR)

    def test_openapi_route(self):
        """
        Test if the /openapi route is properly registered.
        """
        # Setup Test Flask app and Backoffice
        app = Flask(__name__)
        backoffice = Backoffice("app")
        backoffice.build_routes(app)
        ctx = app.app_context()
        ctx.push()
        client = app.test_client()
        # Test the /openapi route
        response = client.get("/app/openapi")
        # Ensure the response is successful and contains JSON data with correct MIME type
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.get_json())

    def test_openapi_basic(self):
        """
        Test the basic OpenAPI specification generation for an empty backoffice.
        - OpenAPI version 3.1.0
        - 3 default schemas: backo-meta, json-patch, backo-filter
        - no routes
        """
        # Setup Test Backoffice
        backoffice = Backoffice("app")
        spec = backoffice.get_openapi()
        # Expecting OpenAPI version 3.1.0
        self.assertEqual(spec["openapi"], "3.1.0")
        # Expecting 3 default schemas: backo-meta, json-patch, backo-filter
        self.assertEqual(len(spec["components"]["schemas"]), 3)
        self.assertIn("backo-meta", spec["components"]["schemas"])
        self.assertIn("json-patch", spec["components"]["schemas"])
        self.assertIn("backo-filter", spec["components"]["schemas"])
        # Expecting no routes
        self.assertEqual(len(spec["paths"]), 0)

    def test_openapi_simple_collection(self):
        """
        Test OpenAPI specification generation for a backoffice with a simple collection.
        """
        # Setup Test Backoffice with a simple test Collection
        backoffice = Backoffice("app")
        backoffice.register_collection(
            Collection(
                "test",
                Item(
                    {
                        "str": String(),
                        "float": Float(),
                        "int": Int(),
                        "bool": Bool(),
                        "blobfile": BlobFile(),
                    }
                ),
                self.__connector,
            )
        )
        backoffice.build_routes(Flask(__name__))
        spec = backoffice.get_openapi()
        # expecting the test schema to be present in the components
        self.assertIn("test", spec["components"]["schemas"])
        # expecting all properties to be present in the test schema with the correct type
        schemas = spec["components"]["schemas"]
        for properties, type in zip(
            ["_id", "_meta", "str", "float", "int", "bool", "blobfile"],
            ["string", "object", "string", "number", "integer", "boolean", "string"],
        ):
            self.assertIn(properties, schemas["test"]["properties"])
            self.assertEqual(
                schemas["test"]["properties"][properties]["type"],
                type,
            )
        # expecting the _meta property to be a reference to the test__meta schema
        self.assertEqual(
            schemas["test"]["properties"]["_meta"]["$ref"],
            "#/components/schemas/test__meta",
        )
        # expecting the blobfile property to have contentEncoding set to base64
        self.assertEqual(
            schemas["test"]["properties"]["blobfile"]["contentEncoding"],
            "base64",
        )
        # expecting no required properties in the test schema
        self.assertEqual(len(schemas["test"]["required"]), 0)
        # expecting the title of the test schema to be "test"
        self.assertEqual(schemas["test"]["title"], "test")

        # expecting routes to be present for the test collection
        self.assertEqual(len(spec["paths"]), 6)
        ## get and post on /test
        self.assertIn("/test", spec["paths"])
        self.assertEqual(len(spec["paths"]["/test"]), 2)
        for method in ["get", "post"]:
            self.assertIn(method, spec["paths"]["/test"])
        ## post on /test/_meta
        self.assertIn("/test/_meta", spec["paths"])
        self.assertEqual(len(spec["paths"]["/test/_meta"]), 1)
        self.assertIn("post", spec["paths"]["/test/_meta"])
        ## post on /test/_check
        self.assertIn("/test/_check", spec["paths"])
        self.assertEqual(len(spec["paths"]["/test/_check"]), 1)
        self.assertIn("post", spec["paths"]["/test/_check"])
        ## get, put, patch, delete on /test/{id}
        self.assertIn("/test/{id}", spec["paths"])
        self.assertEqual(len(spec["paths"]["/test/{id}"]), 4)
        for method in ["get", "put", "patch", "del"]:
            self.assertIn(method, spec["paths"]["/test/{id}"])
        ## get on /test/{id}/{path}
        self.assertIn("/test/{id}/{path}", spec["paths"])
        self.assertEqual(len(spec["paths"]["/test/{id}/{path}"]), 1)
        self.assertIn("get", spec["paths"]["/test/{id}/{path}"])
        ## get and post on /test/_selections/_all
        self.assertIn("/test/_selections/_all", spec["paths"])
        self.assertEqual(len(spec["paths"]["/test/_selections/_all"]), 2)
        for method in ["get", "post"]:
            self.assertIn(method, spec["paths"]["/test/_selections/_all"])

    def test_openapi_action(self):
        """
        Test OpenAPI specification generation for a backoffice with a simple action.
        """
        # Setup Test Backoffice with a simple test Collection
        backoffice = Backoffice("app")
        coll = Collection(
            "test",
            Item({"str": String()}),
            self.__connector,
        )
        backoffice.register_collection(coll)
        coll.register_action("do", Action({"str": String()}, lambda action, item: None))
        backoffice.build_routes(Flask(__name__))
        spec = backoffice.get_openapi()

        self.assertIn("/test/_actions/do/{id}", spec["paths"])
        self.assertIn("post", spec["paths"]["/test/_actions/do/{id}"])
        request_body = spec["paths"]["/test/_actions/do/{id}"]["post"]["requestBody"]
        schema = request_body["content"]["application/json"]["schema"]
        self.assertIn("str", schema["properties"])
        self.assertEqual(schema["properties"]["str"]["type"], "string")

    def test_openapi_selection(self):
        """
        Test OpenAPI specification generation for a backoffice with a simple selection.
        """
        # Setup Test Backoffice with a simple test Collection
        backoffice = Backoffice("app")
        coll = Collection(
            "test",
            Item({"value": Float()}),
            self.__connector,
        )
        backoffice.register_collection(coll)
        coll.register_selection("see", Selection(["$.value"]))
        backoffice.build_routes(Flask(__name__))
        spec = backoffice.get_openapi()

        self.assertIn("/test/_selections/see", spec["paths"])
        selection_path = spec["paths"]["/test/_selections/see"]
        self.assertIn("post", selection_path)
        self.assertIn("get", selection_path)
        selection_request_body = selection_path["post"]["requestBody"]
        self.assertEqual(
            selection_request_body["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/backo-filter",
        )
