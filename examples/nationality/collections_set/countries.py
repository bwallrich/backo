"""Books module"""

# pylint: disable=unused-argument, logging-fstring-interpolation

from backo import (
    Dict,
    String,
    Collection,
    Item,
    GenericMetaDataHandler,
    log_system,
    LogLevel,
)

from .db_country_connector import MyDBRestfullConnector

log = log_system.get_or_create_logger("countries", LogLevel.INFO)


# ------------------------------------------------
# ITEM
# ------------------------------------------------


# --------------------
# Description of "what is a country"
# --------------------
item = Item(
    {
        "name": Dict({"common": String(), "official": String()}),
        "cca2": String(),
        "cca3": String(),
        "flags": Dict({"png": String(), "svg": String(), "alt": String()}),
    },
    meta_data_handler=GenericMetaDataHandler(),
)


# ------------------------------------------------
# COLLECTION
# ------------------------------------------------
connector = MyDBRestfullConnector()

countries = Collection(
    "countries",
    item,
    connector,
    can_create=False,
    can_modify=False,
    can_delete=False,
)


# ------------------------------------------------
# ACTIONS
# ------------------------------------------------

# ------------------------------------------------
# SELECTIONS
# ------------------------------------------------
