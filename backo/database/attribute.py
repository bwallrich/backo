class DatabaseAttribute:
    def __init__(self, connection=None):
        self.connection = connection
        self.attribute_path = None

    def set_default_connection(self, connection):
        if self.connection is None:
            self.connection = connection

    def set_attribute_path(self, attribute_path):
        self.attribute_path = attribute_path

    def search_request(self, base_request, _id):
        pass

    def create_request(self, base_request, value):
        pass

    def update_request(self, base_request, _id, value):
        pass

    def delete_request(self, base_request, _id):
        pass

    def load(self, base_response, attribute_response):
        pass
