"""
The App module
"""
# pylint: disable=logging-fstring-interpolation
from .item import Item
from .action import Action
from .error import Error, ErrorType
from .log import log_system

log = log_system.get_or_create_logger("collection")


class Collection:
    """
    The Collection refer to a "table"
    """

    def __init__(self, name, model : Item, db_handler, ):
        """
        available arguments
        """
        self.db_handler = db_handler
        self.name = name
        self.model = model.copy()
        self.model.__dict__["_collection"] = self
        self.model.set_db_handler( db_handler )
        self.empty = self.model.copy()

        # For actions (aka some element work with datas)
        self._actions = {}
        self.app = None

    def new_item(self):
        """
        return an Item
        """
        return self.empty.copy()

    def new(self):
        """
        return an Item
        """
        return self.new_item()

    def create(self, obj: dict, **kwargs):
        """
        Create and save an item into the DB

        transaction_id : The id of the transaction (used for rollback )
        m_path : modification path, to avoid loop with references
        """
        item = self.new_item()
        item.create( obj, **kwargs)
        return item


    def get_other_collection(self, name):
        """
        Return another collection (ised by Ref and RefsList)
        """
        if self.app is None:
            raise Error(
                ErrorType.COLLECTION_NOT_REGISTERED,
                f"collection {self.name} not registered into an app",
            )
        return self.app.collections.get(name)

    def register_action(self, name:str, action: Action):
        """
        add an action to this collection
        this action will be related to an object
        """
        self._actions[name] = action
        action.__dict__['app'] = self.app
        action.__dict__['name'] = name
        action.__dict__['collection'] = self

    def add_action(self, name:str, action: Action):
        """
        add an action to this collection
        this action will be related to an object
        """
        return self.register_action(name, action)

    def drop(self):
        """
        Drop all elements
        """
        self.db_handler.drop()

    def select(self, select_filter, page_size = 0, num_of_element_to_skip = 0, sort_object = { '_id' : 1 }):
        """
        Do a selection
        """
        result = self.db_handler.select( select_filter, {}, page_size, num_of_element_to_skip , sort_object )
        if not isinstance(result, dict):
            raise Error(
                ErrorType.SELECT_ERROR,
                f"select {self.name} error",
            )
        result['result'] = []
        for obj in result.get('raw', []):
            obj['_id'] = str( obj['_id'] )
            o = self.new_item()
            o.set( obj )
            result['result'].append( o )
        del result['raw']
        return result
