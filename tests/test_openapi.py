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
    Int,
    Item,
    String,
)

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
        for properties, type in zip(
            ["_id", "_meta", "str", "int", "bool", "blobfile"],
            ["string", "object", "string", "integer", "boolean", "string"],
        ):
            self.assertIn(
                properties, spec["components"]["schemas"]["test"]["properties"]
            )
            self.assertEqual(
                spec["components"]["schemas"]["test"]["properties"][properties]["type"],
                type,
            )
        # expecting the _meta property to be a reference to the test__meta schema
        self.assertEqual(
            spec["components"]["schemas"]["test"]["properties"]["_meta"]["$ref"],
            "#/components/schemas/test__meta",
        )
        # expecting the blobfile property to have contentEncoding set to base64
        self.assertEqual(
            spec["components"]["schemas"]["test"]["properties"]["blobfile"][
                "contentEncoding"
            ],
            "base64",
        )
        # expecting no required properties in the test schema
        self.assertEqual(len(spec["components"]["schemas"]["test"]["required"]), 0)
        # expecting the title of the test schema to be "test"
        self.assertEqual(spec["components"]["schemas"]["test"]["title"], "test")

        # expecting routes to be present for the test collection
        self.assertEqual(len(spec["paths"]), 6)
        self.assertIn("/test", spec["paths"])
        self.assertIn("/test/_meta", spec["paths"])
        self.assertIn("/test/_check", spec["paths"])
        self.assertIn("/test/{id}", spec["paths"])
        self.assertIn("/test/{id}/{path}", spec["paths"])
        self.assertIn("/test/_selections/_all", spec["paths"])
