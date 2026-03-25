"""
backoffice tests : The main application test
"""

import unittest
import json
import sys

sys.path.insert(1, "../../../backo")
sys.path.insert(1, "../../../stricto")
sys.path.insert(1, "../")


from nationality import flask


class TestBackoffice(unittest.TestCase):
    """
    Tests for this example.
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)
        ctx = flask.app_context()
        ctx.push()
        self.client = flask.test_client()

    def test_get_a_country(self):
        """
        try to get a country
        """
        response = self.client.get("/nationality/coll/countries/can")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["name"]["common"], "Canada")
        self.assertEqual(results["_id"], "CAN")

    def test_get_a_false_country(self):
        """
        try to get a wrong country
        """
        response = self.client.get("/nationality/coll/countries/trumpland")
        self.assertEqual(response.status_code, 404)

    def test_select_country(self):
        """
        try to select country
        """
        response = self.client.get("/nationality/coll/countries?name.common=France")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)

    def test_create_person(self):
        """
        try to create
        """
        response = self.client.post(
            "/nationality/coll/people",
            json={
                "name": "bourne",
                "surname": "jason",
                "first_nationality": "USA",
                "other_nationalities": ["FRA"],
            },
        )
        self.assertEqual(response.status_code, 200)
        d = json.loads(response.data)
        jason_id = d["_id"]

        # delete the user

        response = self.client.delete(f"/nationality/coll/people/{jason_id}")
        self.assertEqual(response.status_code, 200)
