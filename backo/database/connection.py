from abc import ABC, abstractmethod
from .request import DatabaseSearchRequest


class DatabaseConnection(ABC):
    @abstractmethod
    def execute_search(self, query):
        pass

    @abstractmethod
    def execute_create(self, query):
        pass
