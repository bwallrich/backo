# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code, unused-argument

"""
test for File()
"""

import unittest
import tempfile
import base64
import os
import io
import json
from flask import Flask
from werkzeug.datastructures import FileStorage

from backo import (
    Backoffice,
    current_user,
    Collection,
    Item,
    File,
    Dict,
    String,
    DBYmlConnector,
    FileError,
    StrictoEncoder,
    SSyntaxError,
    SConstraintError,
    FileSystemConnector,
    FileBlobConnector,
    BlobFile,
    GenericMetaDataHandler,
)

TEST_PATH = os.path.join(tempfile.gettempdir(), "backo_file_tests")
TEST_PATH2 = os.path.join(tempfile.gettempdir(), "backo_file_tests_2")
SRC_DIR = "/tmp/backo_tests_routes_file_src"
YML_DIR = "/tmp/backo_tests_files"


class TestFile(unittest.TestCase):
    """
    Test File()
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)

        self.clean(TEST_PATH)
        self.clean(TEST_PATH2)

        if not os.path.exists(TEST_PATH):
            os.makedirs(TEST_PATH)
        if not os.path.exists(TEST_PATH2):
            os.makedirs(TEST_PATH2)
        if not os.path.exists(SRC_DIR):
            os.makedirs(SRC_DIR)

        dirs = os.listdir(TEST_PATH)
        for file in dirs:
            os.unlink(os.path.join(TEST_PATH, file))

        self.work_connector = FileSystemConnector(path=TEST_PATH)

        self.yml_users = DBYmlConnector(path=YML_DIR)
        self.yml_users.generate_id = lambda o: f"User_{o.name}_{o.surname}"

    def clean(self, path: str):
        """Erase all"""
        if not os.path.exists(path):
            return
        dirs = os.listdir(path)
        for file in dirs:
            os.unlink(os.path.join(path, file))
        os.rmdir(path)

    @classmethod
    def tearDownClass(cls):
        """Erase all"""
        cls.clean(cls, TEST_PATH)
        cls.clean(cls, TEST_PATH2)

    def test_error_dir_not_exists(self):
        """
        Test error type
        """
        with self.assertRaises(SSyntaxError) as e:
            File(work=FileSystemConnector(path="/paths_error_not_exists"))
        self.assertEqual(
            e.exception.to_string(),
            'File path "/paths_error_not_exists" is not a directory',
        )

    def sub_test_error_read(self, file_type):
        """
        Test error type
        """
        a = file_type
        a.filename = "notexists.txt"
        with self.assertRaises(FileError) as e:
            a.get_content()
        self.assertEqual(e.exception.to_string(), "$ file doesnt exists (no file_id)")

    def test_error_read(self):
        """
        Test error read
        """
        for file_connector in [
            BlobFile(),
            File(work=self.work_connector),
            File(work=FileBlobConnector()),
        ]:
            with self.subTest(file_connector=file_connector):
                self.sub_test_error_read(file_connector)

    def sub_test_set_get_sample(self, file_type):
        """
        Test set type
        """
        a = file_type
        a.filename = "toto.txt"
        a.set_content("coucou")
        self.assertEqual(a.content_type.get_value(), "text/plain")
        self.assertEqual(a.filename.get_value(), "toto.txt")
        self.assertEqual(a.get_content(), b"coucou")

    def test_set_get_sample(self):
        """
        Test sample get
        """
        for file_connector in [
            BlobFile(),
            File(work=self.work_connector),
            File(work=FileBlobConnector()),
        ]:
            with self.subTest(file_connector=file_connector):
                self.sub_test_set_get_sample(file_connector)

    def sub_test_copy(self, file_type):
        """
        Test copy
        """
        a = file_type
        a.set_content(b"coucou")
        self.assertEqual(a.get_content(), b"coucou")
        b = a.copy()
        self.assertEqual(b.get_content(), b"coucou")
        a.set_content(b"coucou 2")
        self.assertNotEqual(a.get_content(), b.get_content())

    def test_copy(self):
        """
        test copy object file into another
        """
        for file_connector in [
            BlobFile(),
            File(work=self.work_connector),
            File(work=FileBlobConnector()),
        ]:
            with self.subTest(file_connector=file_connector):
                self.sub_test_copy(file_connector)

    def sub_test_file_in_dict(self, file_type):
        """
        Test file in a Dict
        """

        a = Dict({"f": file_type, "name": String()})
        a.set({"name": "Charlie"})
        self.assertEqual(a.f.get_content(), b"Hello Charlie.")
        b = a.copy()
        # sa = json.dumps(a, cls=StrictoEncoder)  # json dumps
        # b.set(json.loads(sa))

        self.assertEqual(b.f.get_content(), b"Hello Charlie.")
        b.name = "Bravo"
        self.assertEqual(b.f.get_content(), b"Hello Bravo.")
        self.assertEqual(a.f.get_content(), b"Hello Charlie.")
        sa = json.dumps(a, cls=StrictoEncoder)  # json dumps
        b.set(json.loads(sa))
        self.assertEqual(b.f.get_content(), b"Hello Charlie.")
        self.assertEqual(a.f.get_content(), b"Hello Charlie.")

    def test_file_in_dict(self):
        """Test update file in a Dict"""

        def update_file(o: Dict):
            o.f.set_content(f"Hello {o.name}.")
            return o.f

        for file_connector in [
            BlobFile(set=update_file),
            File(work=self.work_connector, set=update_file),
            File(work=FileBlobConnector(), set=update_file),
        ]:
            with self.subTest(file_connector=file_connector):
                self.sub_test_file_in_dict(file_connector)

    def sub_test_file_constraints(self, file_type):
        """Check a file with constraint

        :param file_type: _description_
        :type file_type: _type_
        """
        a = file_type
        a.check("toto")
        with self.assertRaises(SConstraintError) as e:
            a.check(b"\x01\x02\x03\x04\x05\x06")
        self.assertEqual(
            e.exception.to_string(),
            "$: Constraint not validated for value=\"<FileStorage: None ('application/octet-stream')>\"",
        )

    def test_file_constraints(self):
        """Test constraints on a file"""

        def only_text(f: FileStorage | None, o) -> bool:
            """check manualy if the mime type is text/plain"""
            if f is None:
                return True
            if f.content_type == "text/plain":
                return True
            return False

        for file_connector in [
            BlobFile(constraint=only_text),
            File(work=self.work_connector, constraint=only_text),
            File(work=FileBlobConnector(), constraint=only_text),
        ]:
            with self.subTest(file_connector=file_connector):
                self.sub_test_file_constraints(file_connector)

        for file_connector in [
            BlobFile(mime_types=["text/plain"]),
            File(work=self.work_connector, mime_types=["text/plain"]),
            File(work=FileBlobConnector(), mime_types=["text/plain"]),
        ]:
            with self.subTest(file_connector=file_connector):
                a = file_connector
                a.check("toto")
                with self.assertRaises(SConstraintError) as e:
                    a.check(b"\x01\x02\x03\x04\x05\x06")
                self.assertEqual(
                    e.exception.to_string(),
                    '$: Unauthorized content_type (value="application/octet-stream")',
                )

        for file_connector in [
            BlobFile(max=4),
            File(work=self.work_connector, max=4),
            File(work=FileBlobConnector(), max=4),
        ]:
            with self.subTest(file_connector=file_connector):
                a = file_connector
                a.check("tot")
                with self.assertRaises(SConstraintError) as e:
                    a.check(b"\x01\x02\x03\x04\x05\x06")
                self.assertEqual(
                    e.exception.to_string(),
                    "$: File too big (value=\"<FileStorage: None ('application/octet-stream')>\")",
                )

    def test_filestorage_src_blobfile(self):
        """test fileStorage as source"""
        data = bytes([1, 2, 3, 4, 5, 6])
        file = FileStorage(
            stream=io.BytesIO(data),
            filename="filename.dat",
            content_type="application/octet-stream",
            content_length=len(data),
        )
        a = BlobFile()
        a.set_content(file)
        self.assertEqual(a.get_content(), b"\x01\x02\x03\x04\x05\x06")

    def test_filestorage_src_file(self):
        """test fileStorage as source"""
        data = bytes([1, 2, 3, 4, 5, 6])
        file = FileStorage(
            stream=io.BytesIO(data),
            filename="filename.dat",
            content_type="application/octet-stream",
            content_length=len(data),
        )
        a = File(work=self.work_connector)
        a.filename = "output_filestorage.txt"
        a.set_content(file)
        self.assertEqual(a.get_content(), b"\x01\x02\x03\x04\x05\x06")

    def test_file_full_cold(self):
        """
        Test copy
        """
        backoffice = Backoffice("myApp")

        backoffice.register_collection(
            Collection(
                "users",
                Item(
                    {
                        "name": String(),
                        "surname": String(),
                        "f": File(
                            work=self.work_connector,
                            storage=FileSystemConnector(path=TEST_PATH2),
                        ),
                    }
                ),
                self.yml_users,
            )
        )

        self.yml_users.drop()

        current_user.standalone = True
        u = backoffice.users.create({"name": "bebert", "surname": "bebert"})
        u.f.set_content(b"coucou22")
        u.save()

        v = backoffice.users.new()
        v.load(u._id.get_value())
        self.assertEqual(v.f.get_content(), b"coucou22")

    def build_backoffice(self, item: Item):
        """Factorisation of the backoffice build for routes"""
        backoffice = Backoffice("myApp")

        backoffice.register_collection(Collection("users", item, self.yml_users))

        self.yml_users.drop()

        # set the flask route
        flask = Flask(__name__)
        backoffice.build_routes(flask)

        # Set client for testing
        ctx = flask.app_context()
        ctx.push()
        client = flask.test_client()
        return client

    def sub_test_file_routes(self, file_type):
        """
        Test route ith a blobfile
        """
        model = Item(
            {
                "name": String(),
                "surname": String(),
                "f": file_type,
            },
            meta_data_handler=GenericMetaDataHandler(),
        )

        client = self.build_backoffice(model)

        # Creation with a FileStorage
        fname = os.path.join(SRC_DIR, "demofile.txt")
        with open(fname, "w", encoding="utf-8") as f:
            f.write("Now the file has more content!")

        response = client.post(
            "/myApp/users",
            data={
                "_json": json.dumps({"name": "bert3", "surname": "hector"}),
                "f": io.FileIO(fname, "rb"),
            },
        )
        self.assertEqual(response.status_code, 200)
        v = json.loads(response.data)
        response = client.get(f"/myApp/users/{v['_id']}")
        self.assertEqual(response.status_code, 200)
        u = model.copy()
        u.set(json.loads(response.data))
        self.assertEqual(u.f.get_content(), b"Now the file has more content!")
        # delete
        response = client.delete(f"/myApp/users/{v['_id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(u.f._work_connector.has_file(u.f.file_id.get_value()), False)

        # creation with a file in string.
        v = "yeswecanornot"
        response = client.post(
            "/myApp/users", json={"name": "bert3", "surname": "hector", "f": v}
        )
        self.assertEqual(response.status_code, 200)
        v = json.loads(response.data)
        response = client.get(f"/myApp/users/{v['_id']}")
        self.assertEqual(response.status_code, 200)
        u = model.copy()
        u.set(json.loads(response.data))
        self.assertEqual(u.f.get_content(), b"yeswecanornot")
        # delete
        response = client.delete(f"/myApp/users/{v['_id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(u.f._work_connector.has_file(u.f.file_id.get_value()), False)

        # creation with a file in base64.
        v = b"yeswecanornot"
        response = client.post(
            "/myApp/users",
            json={
                "name": "bert3",
                "surname": "hector3",
                "f": f"base64:{base64.b64encode(v).decode('utf-8')}",
            },
        )
        self.assertEqual(response.status_code, 200)
        v = json.loads(response.data)
        response = client.get(f"/myApp/users/{v['_id']}")
        self.assertEqual(response.status_code, 200)
        u = model.copy()
        u.set(json.loads(response.data))
        self.assertEqual(u.f.get_content(), b"yeswecanornot")
        # delete
        response = client.delete(f"/myApp/users/{v['_id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(u.f._work_connector.has_file(u.f.file_id.get_value()), False)

    def test_file_routes(self):
        """Test routes"""

        fname = os.path.join(SRC_DIR, "demofile.txt")
        with open(fname, "w", encoding="utf-8") as f:
            f.write("Now the file has more content!")

        for file_connector in [
            BlobFile(),
            File(work=self.work_connector),
            File(work=FileBlobConnector()),
        ]:
            with self.subTest(file_connector=file_connector):
                self.sub_test_file_routes(file_connector)
