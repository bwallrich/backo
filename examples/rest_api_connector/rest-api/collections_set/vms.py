"""Virtual Machines collection set."""

from constants import get_data_dir
from backo import (
    String,
    Collection,
    Item,
    GenericMetaDataHandler,
    DBYmlConnector,
)

vms_store = DBYmlConnector(path=str(get_data_dir() / "vms"))

vms = Item(
    {"name": String(required=True), "image": String(required=True)},
    meta_data_handler=GenericMetaDataHandler(),
)

vms_coll = Collection("vms", vms, vms_store)
