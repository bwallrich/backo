"""
Test for OpenAPI specification generation.
"""

import unittest

from flask import Flask

from backo import Backoffice


class TestOpenAPI(unittest.TestCase):
    """
    Test OpenAPI specification generation.
    """

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
