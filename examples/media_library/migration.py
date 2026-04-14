"""
migration sample script


"""

import sys

sys.path.insert(1, "../../../backo")
sys.path.insert(1, "../../../stricto")
sys.path.insert(1, "../")


from media_library import myapp
from backo import log_system, LogLevel

# Set migration level to debug
log_migration = log_system.get_or_create_logger("migration", LogLevel.DEBUG)


# ---------------------------------------------
# Check if a data match the model
# it raise an error if not
# ---------------------------------------------
report = myapp.migrate("books", _id="my_book_id")
report = myapp.migrate("books", _ids=["my_book_id1", "my_book_id2"])
report = myapp.migrate("books")  # All ids


# --------------------------------------------
# Do a changement
# example you must now have a note field with a float value
# --------------------------------------------
def update_with_note(o: dict) -> dict:
    """
    this the function for doing operation on objects before setting them into the Item
    You can do what you want.
    """
    if "note" not in o:
        o["note"] = 10.0
    return o


# Check if OK (dry_run is True by default)
report = myapp.migrate("books", update_with_note, _id="my_book_id")
report = myapp.migrate("books", update_with_note, _ids=["my_book_id1", "my_book_id2"])
report = myapp.migrate("books", update_with_note)  # All ids

# do it for real
report = myapp.migrate("books", update_with_note, _id="my_book_id", dry_run=False)
report = myapp.migrate(
    "books", update_with_note, _ids=["my_book_id1", "my_book_id2"], dry_run=False
)
report = myapp.migrate("books", update_with_note, dry_run=False)  # All ids
