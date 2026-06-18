from ..database.engine import DatabaseEngine
from .connection import YamlConnection
from .item import YamlItem


class YamlEngine(DatabaseEngine):
    def __init__(self, file_path, yaml_path=[], database_item=YamlItem()):
        super().__init__(YamlConnection(file_path, yaml_path), database_item)
