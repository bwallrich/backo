import uuid

from backo.utils.nested_data_path import find, update, delete
from ..database.item import ItemMapper, DatabaseItem
from ..database.attribute import DatabaseAttribute

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

class YamlAttribute(DatabaseAttribute):
    def __init__(self, path):
        """
        :param attribute: Name of the field to load from the Yaml file
        """
        self.path = path

    def search_request(self, base_request, _id):
        # Nothing to do, the requested field will already be included in the
        # response of the base_request, that include the complete object
        # associated to _id
        pass

    def load(self, base_response, _attribute_response):
        # _attribute_response is None, because no request was returned by
        # search_request. But the field can be retrieved from the response of
        # the base request
        value = find(base_response.value, self.path)
        # The value must be deleted from the response so this field is not
        # included in the generated JSON-like dict
        delete(base_response.value, self.path)
        return value

    def create_request(self, base_request: YamlCreateRequest, value):
        # Adds the value of the attribute to the base create request
        update(base_request.value, self.path, value)
        # Removes the replaced path from the original user item
        delete(base_request.value, self.attribute_path)

    def update_request(self, base_request, _id, value):
        # Adds the value of the attribute to the base create request
        update(base_request.value, self.path, value)
        # Removes the replaced path from the original user item
        delete(base_request.value, self.attribute_path)

    def delete_request(self, base_request, _id):
        # Nothing to do, the complete item will be deleted by the base request
        pass
