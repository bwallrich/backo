import uuid

from ..database.item import ItemMapper, DatabaseItem
from .request import (
    YamlSearchRequest,
    YamlCreateRequest,
    YamlDeleteRequest,
    YamlUpdateRequest,
)


def uuid4():
    return str(uuid.uuid4())


class MapByKey(ItemMapper):
    def __init__(self, generate_id=uuid4):
        self.generate_id = generate_id

    def created_id(self, yaml_create_response):
        return yaml_create_response.created_id

    def search_request(self, _id):
        return YamlSearchRequest([_id])

    def create_request(self, item_value):
        _id = self.generate_id()
        return YamlCreateRequest([_id], item_value, _id)

    def delete_request(self, _id):
        return YamlDeleteRequest([_id])

    def update_request(self, _id, value):
        return YamlUpdateRequest([_id], value)

    def load(self, base_search_response):
        return base_search_response.value


class YamlItem(DatabaseItem):
    def __init__(
        self, item_mapper=MapByKey(), model={}
    ):
        super().__init__(item_mapper, model)
