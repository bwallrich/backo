"""
Test for OpenAPI specification generation.
"""

import unittest
from typing import Callable

from flask import Flask
from flask.testing import FlaskClient

from backo import Backoffice


def _build_test_client(backoffice_generator: Callable[[], Backoffice]) -> FlaskClient:
    """
    Build a test client for the given backoffice generator.

    :param backoffice_generator: A callable that returns a Backoffice instance.
    :type backoffice_generator: Callable[[], Backoffice]
    :return: A Flask test client.
    :rtype: FlaskClient
    """
    app = Flask(__name__)
    backoffice = backoffice_generator()
    backoffice.build_routes(app)
    ctx = app.app_context()
    ctx.push()
    return app.test_client()


class TestOpenAPI(unittest.TestCase):
    """
    Test OpenAPI specification generation.
    """

    def test_openapi_basic(self):
        """
        Test the generation of OpenAPI specification.
        """
        client = _build_test_client(lambda: Backoffice("app"))
        response = client.get("/app/openapi")  # Trigger the OpenAPI generation
        self.assertEqual(response.status_code, 200)
        spec = response.get_json()
        # Expecting OpenAPI version 3.1.0
        self.assertEqual(spec["openapi"], "3.1.0")
        # Expecting 3 default schemas: backo-meta, json-patch, backo-filter
        self.assertEqual(len(spec["components"]["schemas"]), 3)
        self.assertIn("backo-meta", spec["components"]["schemas"])
        self.assertIn("json-patch", spec["components"]["schemas"])
        self.assertIn("backo-filter", spec["components"]["schemas"])
        # Expecting no routes
        self.assertEqual(len(spec["paths"]), 0)
