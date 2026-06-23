class ItemMapper:
    def created_id(self, create_response) -> str:
        raise NotImplementedError("This ItemMapper does not support item creation")

    def search_request(self, _id):
        raise NotImplementedError("This ItemMapper does not support item search")

    def create_request(self, item_value):
        raise NotImplementedError("This ItemMapper does not support item creation")

    def delete_request(self, _id):
        raise NotImplementedError("This ItemMapper does not support item deletion")

    def update_request(self, _id, item_value):
        raise NotImplementedError("This ItemMapper does not support item update")

    def load(self, _base_response):
        return {}
