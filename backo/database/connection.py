from typing import Any
from abc import ABC, abstractmethod
from .request import DatabaseSearchRequest


class DatabaseConnection(ABC):
    @abstractmethod
    def execute_search(self, query: DatabaseSearchRequest) -> Any:
        pass
