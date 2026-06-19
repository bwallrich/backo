from .request import DatabaseSearchRequest


class DatabaseConnection:
    def execute_search(self, query):
        raise NotImplementedError(
            "This DatabaseConnection does not support item search"
        )

    def execute_create(self, query):
        raise NotImplementedError(
            "This DatabaseConnection does not support item creation"
        )

    def execute_delete(self, query):
        raise NotImplementedError(
            "This DatabaseConnection does not support item deletion"
        )

    def execute_update(self, query):
        raise NotImplementedError(
            "This DatabaseConnection does not support item update"
        )
