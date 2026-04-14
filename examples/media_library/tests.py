"""
backoffice tests : The main application test
"""

import unittest
import json
import sys
from datetime import datetime, timedelta

sys.path.insert(1, "../../../backo")
sys.path.insert(1, "../../../stricto")
sys.path.insert(1, "../")


from media_library import flask
from backo import log_system, LogLevel

log_system.setLevel(LogLevel.ERROR)


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

    def login(self, login):
        """Do a login"""
        return self.client.post("/login", json={"login": login, "password": login})

    def logout(self):
        """Do a logout"""
        return self.client.get("/logout")

    def test_jwt_fail(self):
        """test jwt error"""
        self.logout()
        response = self.client.get("/ping")
        self.assertEqual(response.status_code, 401)

    def test_login_logout(self):
        """
        test login logout
        """
        self.logout()
        self.login("test")
        self.logout()
        response = self.client.get("/ping")
        self.assertEqual(response.status_code, 401)

    def test_emp1_cannot_create_a_user(self):
        """
        test error user creation
        """
        self.logout()
        response = self.login("emp1")
        response = self.client.post("/media_library/users", json={"login": "toto1"})
        self.assertEqual(response.status_code, 403)
        self.logout()

    def test_admin_create_users(self):
        """
        create a user
        """
        self.logout()
        response = self.login("admin")
        response = self.client.post("/media_library/users", json={"login": "toto1"})
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/media_library/users", json={"login": "toto2"})
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/media_library/users", json={"login": "toto3"})
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/media_library/users", json={"login": "toto4"})
        self.assertEqual(response.status_code, 200)
        self.logout()

    def test_emp1_add_books(self):
        """
        test add a book
        """
        self.logout()
        response = self.login("emp1")
        response = self.client.post(
            "/media_library/books",
            json={"title": "martine a la plage 1", "pages": 21},
        )
        self.assertEqual(response.status_code, 200)
        d = json.loads(response.data)
        book_id = d["_id"]
        # self.logout()
        # self.login('test')
        # response=self.client.delete(f"/media_library/books/{book_id}")
        # self.assertEqual(response.status_code, 403)
        # self.logout()
        # self.login('emp1')
        response = self.client.delete(f"/media_library/books/{book_id}")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/media_library/books",
            json={"title": "martine a la plage 2", "pages": 22},
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/media_library/books",
            json={"title": "martine a la plage 3", "pages": 23},
        )
        self.assertEqual(response.status_code, 200)
        self.logout()

    def test_emp1_borrow_a_book(self):
        """
        Test borrow a book
        """
        self.logout()
        response = self.login("emp1")
        response = self.client.get("/media_library/users?login=toto1")
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)
        user = results["result"][0]
        response = self.client.get("/media_library/books?title.$reg=martine.*3")
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)
        book = results["result"][0]
        # response = self.client.post(
        #     f"/media_library/books/_actions/borrow/{book['_id']}",
        #     json={"user_id": user['_id'], "return_date": "test"},
        # )
        # self.assertEqual(response.status_code, 400)
        return_date = datetime.now() + timedelta(days=3)
        response = self.client.post(
            f"/media_library/books/_actions/borrow/{book['_id']}",
            json={"user_id": user["_id"], "return_date": return_date.isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f"/media_library/users/{user['_id']}")
        u = json.loads(response.data)
        self.assertEqual(u["rent"]["books"][0], book["_id"])

        # verify book has borrowed = True
        response = self.client.get(f"/media_library/books/{book['_id']}")
        b = json.loads(response.data)
        self.assertEqual(b["borrowed"], True)

        # Do the selection on borrowed books
        response = self.client.get("/media_library/books/_selections/borrowed")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)
        self.assertEqual(results["result"][0][2], "toto1")
