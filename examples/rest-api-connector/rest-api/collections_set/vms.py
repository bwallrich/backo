from backo import (
    Dict,
    String,
    Int,
    Collection,
    Item,
    Ref,
    RefsList,
    Collection,
    DeleteStrategy,
    GenericMetaDataHandler,
    log_system,
    LogLevel,
    DBYmlConnector,
)
from constants import get_data_dir

vms_store = DBYmlConnector(path=str(get_data_dir() / "vms"))

vms = Item(
    {"name": String(required=True), "image": String(required=True)},
    meta_data_handler=GenericMetaDataHandler(),
)

vms_coll = Collection("vms", vms, vms_store)
