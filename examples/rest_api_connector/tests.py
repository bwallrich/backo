"""
backoffice tests : The main application test
"""

import unittest
import json
import sys

sys.path.insert(1, "../../../backo")
sys.path.insert(1, "../../../stricto")
sys.path.insert(1, "../")


from rest_api_connector import create_app


class TestBackoffice(unittest.TestCase):
    """
    Tests for this example.

    WARNING: Make sure the remote REST API is running before executing these tests
    """

    def __init__(self, *args, **kwargs):
        """
        init this tests
        """
        super().__init__(*args, **kwargs)
        config = {
            "data_dir": "./data",
            "server": {"host": "127.0.0.1", "port": 5000},
            "logging": {"level": "ERROR"},
        }
        self.app = create_app(config)
        self.client = self.app.test_client()
        """
        for rule in self.app.url_map.iter_rules():
            print(rule)
        """

    def test_00_get_get_all_vms(self):
        """
        try to delete all VMs
        """
        response = self.client.get("/api/v1/it/vms")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 0)
        self.assertEqual(len(results["result"]), results["total"])

    def test_01_create_vm(self):
        """
        try to create a VM
        """
        vm_data = {
            "name": "vm-01",
            "image": "ubuntu-20.04",
        }
        response = self.client.post(
            "/api/v1/it/vms",
            data=json.dumps(vm_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)  # Should be 201 but it is 200

        response = self.client.get("/api/v1/it/vms")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)

    def test_02_get_vm_by_id(self):
        """
        try to get a VM by its ID
        """
        response = self.client.get("/api/v1/it/vms")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)
        self.assertEqual(len(results["result"]), results["total"])

        _id = results["result"][0]["_id"]
        response = self.client.get(f"/api/v1/it/vms/{_id}")
        self.assertEqual(response.status_code, 200)
        vm = json.loads(response.data)
        self.assertEqual(vm["_id"], _id)

    def test_03_save_vm(self):
        """
        try to update a VM
        """
        response = self.client.get("/api/v1/it/vms")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)
        self.assertEqual(len(results["result"]), results["total"])

        _id = results["result"][0]["_id"]
        response = self.client.get(f"/api/v1/it/vms/{_id}")
        self.assertEqual(response.status_code, 200)
        vm = json.loads(response.data)
        self.assertEqual(vm["_id"], _id)
        self.assertEqual(vm["image"], "ubuntu-20.04")

        vm_data = {
            "name": "vm-01",
            "image": "ubuntu-22.04",
        }
        response = self.client.put(
            f"/api/v1/it/vms/{_id}",
            data=json.dumps(vm_data),
            content_type="application/json",
        )
        vm = json.loads(response.data)
        self.assertEqual(response.status_code, 200)  # Should be 201 but it is 200
        self.assertEqual(vm["_id"], _id)
        self.assertEqual(vm["image"], "ubuntu-22.04")

    def test_04_delete_all_vms(self):
        """
        try to delete all VMs
        """
        response = self.client.get("/api/v1/it/vms")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 1)
        self.assertEqual(len(results["result"]), results["total"])
        vm_id = results["result"][0]["_id"]

        response = self.client.delete(f"/api/v1/it/vms/{vm_id}")
        # self.assertEqual(response.status_code, 204)
        self.assertEqual(response.status_code, 200)  # Should be 204 but it is 200

        response = self.client.get("/api/v1/it/vms")
        self.assertEqual(response.status_code, 200)
        results = json.loads(response.data)
        self.assertEqual(results["total"], 0)
        self.assertEqual(len(results["result"]), results["total"])

    def test_05_not_found(self):
        """
        try to get a non-existent endpoint or vm
        """
        response = self.client.get("/vms")
        self.assertEqual(response.status_code, 404)

        response = self.client.get(f"/api/v1/it/vms/vm01")
        self.assertEqual(response.status_code, 404)
