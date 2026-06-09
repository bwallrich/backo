"""Users module"""

# pylint: disable=unused-argument, logging-fstring-interpolation

from constants import get_data_dir
from backo import (
    String,
    Collection,
    Item,
    DBYmlConnector,
    GenericMetaDataHandler,
    log_system,
    LogLevel,
    RefsList,
)

log = log_system.get_or_create_logger("users", LogLevel.INFO)


# ------------------------------------------------
# ITEM
# ------------------------------------------------


# ------------------------------------
# Description of the Item
#
# The item is the object in the collection
# ------------------------------------
item = Item(
    {
        "name": String(require=True),
        "surname": String(require=True),
        "login": String(require=True),
        "vms": RefsList(coll="vms"),
    },
    meta_data_handler=GenericMetaDataHandler(),
)

# ------------------------------------------------
# COLLECTION
# ------------------------------------------------

# First define the connector  = where to store datas
connector = DBYmlConnector(path=str(get_data_dir() / "users"))


#
# The collection creation
#
# Association of Item, collector, rights
#
users = Collection(
    "users",
    item,
    connector,
)


# ------------------------------------------------
# SELECTIONS
# ------------------------------------------------
