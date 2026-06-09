"""Books module"""

# pylint: disable=unused-argument, logging-fstring-interpolation

from backo import (
    String,
    Collection,
    Item,
    GenericMetaDataHandler,
    log_system,
    LogLevel,
)

from .vms_connector import VMsConnector

log = log_system.get_or_create_logger("vms", LogLevel.INFO)


# ------------------------------------------------
# ITEM
# ------------------------------------------------


# --------------------
# Description of "what is a vm"
# --------------------
item = Item(
    {
        "name": String(),
        "image": String(),
    },
    meta_data_handler=GenericMetaDataHandler(),
)


# ------------------------------------------------
# COLLECTION
# ------------------------------------------------
connector = VMsConnector()

vms = Collection("vms", item, connector)


# ------------------------------------------------
# ACTIONS
# ------------------------------------------------

# ------------------------------------------------
# SELECTIONS
# ------------------------------------------------
