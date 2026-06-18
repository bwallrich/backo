import pathlib
from yaml import load, dump, Loader, Dumper
from backo.utils.nested_data_path import find, update, delete

from ..database.connection import DatabaseConnection
from .request import (
    YamlSearchRequest,
    YamlSearchResponse,
    YamlCreateRequest,
    YamlCreateResponse,
    YamlDeleteRequest,
    YamlDeleteResponse,
    YamlUpdateRequest,
    YamlUpdateResponse,
)
from ..error import NotFoundError


class YamlConnection(DatabaseConnection):
    def __init__(self, file_path, yaml_path=[]):
        """Connection to a YAML file.

        :param file_path: Path to the YAML file
        :param yaml_path: YAML path to objects considered by the connection
        """
        self.file_path = pathlib.Path(file_path)
        self.yaml_path = yaml_path

    def execute_search(self, yaml_search_request):
        with open(self.file_path, "r") as yaml_database:
            database = load(yaml_database.read(), Loader=Loader)
            try:
                return YamlSearchResponse(
                    yaml_search_request.path,
                    # The request search path is relative to the base YAML path
                    find(database, self.yaml_path + yaml_search_request.path)
                )
            except KeyError as e:
                raise NotFoundError(
                    f"Object with id {yaml_search_request.path} not found in YAML file {self.file_path}"
                )

    def execute_create(self, yaml_create_request):
        database = None
        with open(self.file_path, "r") as yaml_database:
            # Init database as an empty dict if the file is empty
            database = load(yaml_database.read(), Loader=Loader) or {}

        # The path of the item to update is relative to the base YAML path
        update(database, self.yaml_path + yaml_create_request.path, yaml_create_request.value)

        with open(self.file_path, "w") as yaml_database:
            yaml_database.write(dump(database, Dumper=Dumper))
        return YamlCreateResponse(yaml_create_request.created_id)

    def execute_delete(self, yaml_delete_request):
        database = None
        with open(self.file_path, "r") as yaml_database:
            # Init database as an empty dict if the file is empty
            database = load(yaml_database.read(), Loader=Loader) or {}

        try:
            # The path of the item to delete is relative to the base YAML path
            delete(database, self.yaml_path + yaml_delete_request.path)
        except KeyError:
            # Deleting an object that do not exist is not an error
            pass

        with open(self.file_path, "w") as yaml_database:
            yaml_database.write(dump(database, Dumper=Dumper))
        return YamlDeleteResponse()

    def execute_update(self, yaml_update_request):
        database = None
        with open(self.file_path, "r") as yaml_database:
            # Init database as an empty dict if the file is empty
            database = load(yaml_database.read(), Loader=Loader) or {}

        # The path of the item to update is relative to the base YAML path
        update(database, self.yaml_path + yaml_update_request.path, yaml_update_request.value)

        with open(self.file_path, "w") as yaml_database:
            yaml_database.write(dump(database, Dumper=Dumper))
        return YamlDeleteResponse()
