
"""Provides the specification of the DatabaseConnection interface.
"""

class DatabaseConnection:
    """Component used to execute requests on a real database.

    Any request performed by the DatabaseEngine is transparently performed using
    this generic API, and only those methods are responsible to perform each
    operation. This means all efforts required to implement a connection to a
    new database only need to be focus on each method of this class.

    Moreover, each operation is independent so only a subset might be
    implemented overriding each method of this class.

    The type of requests and associated responses depends only on the database
    to connect, but the DatabaseConnection does not enforce any other
    requirement.
    """

    def execute_search(self, request):
        """Executes the search request and returns the corresponding response.
        """
        raise NotImplementedError(
            "This DatabaseConnection does not support item search"
        )

    def execute_create(self, request):
        """Executes the create request and returns the corresponding response.
        """
        raise NotImplementedError(
            "This DatabaseConnection does not support item creation"
        )

    def execute_delete(self, request):
        """Executes the delete request and returns the corresponding response.
        """
        raise NotImplementedError(
            "This DatabaseConnection does not support item deletion"
        )

    def execute_update(self, request):
        """Executes the update request and returns the corresponding response.
        """
        raise NotImplementedError(
            "This DatabaseConnection does not support item update"
        )
