"""Users module"""

# pylint: disable=unused-argument, logging-fstring-interpolation

from backo import (
    String,
    Collection,
    Item,
    DBMongoConnector,
    GenericMetaDataHandler,
    log_system,
    LogLevel,
    Ref,
    RefsList,
)

log = log_system.get_or_create_logger("user", LogLevel.INFO)


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
        "first_nationality": Ref(coll="countries"),
        "other_nationalities": RefsList(coll="countries"),
    },
    meta_data_handler=GenericMetaDataHandler(),
)

# ------------------------------------------------
# COLLECTION
# ------------------------------------------------

# First define the connector  = where to store datas
connector = DBMongoConnector(
    connection_string="mongodb://localhost:27017/country", collection="Users"
)


#
# The collection creation
#
# Association of Item, collector, rights
#
people = Collection(
    "people",
    item,
    connector,
)


# ------------------------------------------------
# SELECTIONS
# ------------------------------------------------
