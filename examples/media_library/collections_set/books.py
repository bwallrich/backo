"""Books module"""

# pylint: disable=unused-argument, logging-fstring-interpolation

from datetime import datetime
from backo import (
    Int,
    Datetime,
    Bool,
    Dict,
    String,
    Collection,
    Item,
    current_user,
    DBMongoConnector,
    log_system,
    LogLevel,
    Ref,
    Action,
    Selection,
)

log = log_system.get_or_create_logger("books", LogLevel.INFO)


# ------------------------------------------------
# ITEM
# ------------------------------------------------


def set_borrowed(book: Item) -> bool:
    """compute if the book is currently borrowed

    :param book: the current book
    :type book: Item
    :return: borrowed or not
    :rtype: bool
    """
    if book.borrow is None:
        return False
    if book.borrow.return_date == None:  # pylint: disable=singleton-comparison
        return False
    if book.borrow.return_date > datetime.now().replace(microsecond=0):
        return True
    return False


def can_read_borrow_user(right_name: str, book: Item) -> bool:
    """Tel if current_user can read the name of the personne who borrow the book

    :param right_name: The name of the right (here ="read")
    :type right_name: str
    :param book: the book
    :type book: Item
    :return: True if current_user can read
    :rtype: bool
    """
    if current_user.has_role(["ADMIN", "EMPLOYEE"]):
        return True
    # print(f'book borrewed = {book}')
    if book.borrow.user._id == current_user._id:
        return True
    return False


def can_modify_borrow(right_name: str, book: Item) -> bool:
    """Tel if current_user can modify the borrow part of the book

    :param right_name: The name of the right (here ="modify")
    :type right_name: str
    :param book: The book
    :type book: Item
    :return: True if can modify
    :rtype: bool
    """
    if current_user.has_role(["ADMIN", "EMPLOYEE"]):
        return True

    if book.borrowed is False:
        return True

    return False


# --------------------
# Description of "what is a book"
# --------------------
books_item = Item(
    {
        "title": String(require=True),
        "pages": Int(),
        "borrowed": Bool(set=set_borrowed),
        "borrow": Dict(
            {
                "user": Ref(
                    coll="users",
                    field="$.rent.books",
                    can_read=can_read_borrow_user,
                ),
                "return_date": Datetime(),
                "date": Datetime(),
            },
            can_modify=can_modify_borrow,
        ),
    }
)


# ------------------------------------------------
# COLLECTION
# ------------------------------------------------
connector = DBMongoConnector(
    connection_string="mongodb://localhost:27017/media_library", collection="Books"
)


def can_create(right_name: str, book: Item) -> bool:
    """Check if can create a book"""

    log.debug(f"can create a book by {current_user.login} ? ")

    if current_user.has_role(["ADMIN", "EMPLOYEE"]):
        return True
    return False


def can_modify(right_name: str, book: Item) -> bool:
    """Check if can modify a book"""

    log.debug(f"can modify a book by {current_user.login} ? ")

    if current_user.has_role(["ADMIN", "EMPLOYEE"]):
        return True
    return False


def can_delete(right_name: str, book: Item) -> bool:
    """Check if can delete a book"""

    log.debug(f"can delete a book by {current_user.login} ? ")

    if current_user.has_role(["ADMIN", "EMPLOYEE"]):
        return True
    return False


books = Collection(
    "books",
    books_item,
    connector,
    can_create=can_create,
    can_modify=can_modify,
    can_delete=can_delete,
)


# ------------------------------------------------
# ACTIONS
# ------------------------------------------------


def borrow(action: Action, book: Item) -> None:
    """borrow the book"""
    book.borrow.user = action.user_id
    book.borrow.date = datetime.now().replace(microsecond=0)
    book.borrow.return_date = action.return_date
    book.save()


def can_borrow(right_name: str, book: Item) -> bool:
    """Tel if current_user can execute the borrow action

    :param right_name: The name of the right (here="execute")
    :type right_name: str
    :param book: The book
    :type book: Item
    :return: True if he can
    :rtype: bool
    """
    if current_user.has_role("EMPLOYEE"):
        return True
    return False


def can_see_borrow_action(right_name: str, book: Item) -> bool:
    """Tel the borrow action is a nonsense ?

    you can borrow a book which is not borrowed.

    :param right_name: The name of the right (here="see")
    :type right_name: str
    :param book: the book
    :type book: Item
    :return: True if borrowed field is false
    :rtype: bool
    """
    return not book.borrowed


#
# Definition of the action
borrow_action = Action(
    {"user_id": String(require=True), "return_date": Datetime(require=True)},
    borrow,
    can_execute=can_borrow,
    can_see=can_see_borrow_action,
)

# Add the action to the book collection
books.register_action("borrow", borrow_action)


# ------------------------------------------------
# SELECTIONS
# ------------------------------------------------
borrowed_book_select = Selection(
    ["$.title", "$.borrow.user.login"], filter={"borrowed": True}
)
books.register_selection("borrowed", borrowed_book_select)
