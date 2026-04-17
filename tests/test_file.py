# pylint: disable=duplicate-code
"""
test for File()
"""

import unittest
import tempfile
import os
import json

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
    FileSystemConnector,
    FileBlobConnector,
    BlobFile,
)

TEST_PATH = os.path.join(tempfile.gettempdir(), "backo_file_tests")
TEST_PATH2 = os.path.join(tempfile.gettempdir(), "backo_file_tests_2")
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
        if not os.path.exists(TEST_PATH):
            os.makedirs(TEST_PATH)
        if not os.path.exists(TEST_PATH2):
            os.makedirs(TEST_PATH2)
        dirs = os.listdir(TEST_PATH)
        for file in dirs:
            os.unlink(os.path.join(TEST_PATH, file))

        self.work_connector = FileSystemConnector(path=TEST_PATH)

        self.yml_users = DBYmlConnector(path=YML_DIR)
        self.yml_users.generate_id = lambda o: f"User_{o.name}_{o.surname}"

    @classmethod
    def tearDownClass(cls):
        """Erase all"""
        dirs = os.listdir(TEST_PATH)
        # for file in dirs:
        #         os.unlink(os.path.join(TEST_PATH, file))
        # os.rmdir( TEST_PATH )

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

    def test_error_read(self):
        """
        Test error type
        """
        a = File(work=self.work_connector, encoding="utf-8")
        a.filename = "notexists.txt"
        with self.assertRaises(FileError) as e:
            a.get_content()
        self.assertEqual(
            e.exception.to_string(), '$ file "notexists.txt" not found in storage'
        )

    def test_set_get_sample(self):
        """
        Test set type
        """
        a = File(work=self.work_connector, encoding="utf-8")
        a.filename = "toto.txt"
        a.set_content("coucou")
        self.assertEqual(a.mime_type.get_value(), "text/plain")
        self.assertEqual(a.filename.get_value(), "toto.txt")
        self.assertEqual(
            os.path.isfile(os.path.join(TEST_PATH, a.filename.get_value())), True
        )
        self.assertEqual(a.get_content(), "coucou")

    def test_read_write_chunk(self):
        """
        Test read file chunk
        """
        a = File(work=self.work_connector, encoding="utf-8")
        a.filename = "toto.txt"
        a.set_content("cou1cou2cou3cou4")
        output = FileSystemConnector(path=TEST_PATH)
        c = self.work_connector.read_chunk(
            os.path.join(TEST_PATH, a.filename.get_value()), 4
        )
        index = 1
        for i in c:
            self.assertEqual(i.decode("utf-8"), "cou" + str(index))
            output.write_chunk(os.path.join(TEST_PATH, "output.txt"), i)
            index += 1
        self.assertEqual(os.path.isfile(os.path.join(TEST_PATH, "output.txt")), True)
        b = File(work=self.work_connector, encoding="utf-8")
        b.filename = "output.txt"
        self.assertEqual(b.get_content(), "cou1cou2cou3cou4")

    def test_copy(self):
        """
        Test copy
        """
        a = File(work=self.work_connector)
        a.set_content("coucou")
        self.assertEqual(a.get_content(), "coucou")
        b = a.copy()
        self.assertEqual(b.get_content(), "coucou")
        a.set_content("coucou 2")
        self.assertNotEqual(a.get_content(), b.get_content())

    def test_file_in_dict(self):
        """
        Test file in a Dict
        """

        def update_file(o: Dict):
            o.f.set_content(f"Hello {o.name}.")
            return o.f

        a = Dict(
            {"f": File(work=self.work_connector, set=update_file), "name": String()}
        )
        a.set({"name": "Charlie"})
        self.assertEqual(a.f.get_content(), "Hello Charlie.")
        b = a.copy()
        # sa = json.dumps(a, cls=StrictoEncoder)  # json dumps
        # b.set(json.loads(sa))

        self.assertEqual(b.f.get_content(), "Hello Charlie.")
        b.name = "Bravo"
        self.assertEqual(b.f.get_content(), "Hello Bravo.")
        self.assertEqual(a.f.get_content(), "Hello Charlie.")
        sa = json.dumps(a, cls=StrictoEncoder)  # json dumps
        b.set(json.loads(sa))
        self.assertEqual(b.f.get_content(), "Hello Charlie.")
        self.assertEqual(a.f.get_content(), "Hello Charlie.")

    def test_copy_blob(self):
        """
        Test copy
        """
        a = File(work=FileBlobConnector(encoding="utf-8"), storage=self.work_connector)
        a.set_content("coucou")
        self.assertEqual(a.get_content(), "coucou")
        b = a.copy()
        self.assertEqual(b.get_content(), "coucou")
        a.set_content("coucou 2")
        self.assertNotEqual(a.get_content(), b.get_content())
        a.save()
        a.load()
        self.assertEqual(a.get_content(), "coucou 2")

    def test_blob_only(self):
        """
        Test copy
        """
        a = BlobFile()
        a.set_content("coucou")
        self.assertEqual(a.get_content(), "coucou")
        self.assertEqual(a.content.get_value(), b"coucou")

        a.content.set(b"yolo")
        self.assertEqual(a.get_content(), "yolo")

    def test_blob_full(self):
        """
        Test copy
        """
        backoffice = Backoffice("myApp")

        backoffice.register_collection(
            Collection(
                "users",
                Item({"name": String(), "surname": String(), "f": BlobFile()}),
                self.yml_users,
            )
        )

        self.yml_users.drop()

        current_user.standalone = True
        u = backoffice.users.create({"name": "bebert", "surname": "bebert"})
        u.f.set_content("coucou")
        raw = u.f.content.get_value()
        u.save()
        self.assertEqual(u.f.content.get_value(), raw)
        v = backoffice.users.new()
        v.load(u._id.get_value())
        self.assertEqual(v.f.content.get_value(), raw)
        self.assertEqual(v.f.get_content(), "coucou")

    def test_file_full(self):
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
                        "f": File(work=self.work_connector),
                    }
                ),
                self.yml_users,
            )
        )

        self.yml_users.drop()

        current_user.standalone = True
        u = backoffice.users.create({"name": "bebert", "surname": "bebert"})
        u.f.set_content("coucou")
        u.save()
        v = backoffice.users.new()
        v.load(u._id.get_value())
        self.assertEqual(v.f.get_content(), "coucou")

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
        u.f.set_content("coucou22")
        u.save()

        v = backoffice.users.new()
        v.load(u._id.get_value())
        self.assertEqual(v.f.get_content(), "coucou22")
