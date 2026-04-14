"""Users module"""

# pylint: disable=unused-argument, logging-fstring-interpolation

from backo import (
    String,
    List,
    Dict,
    Collection,
    Item,
    current_user,
    DBMongoConnector,
    Action,
    log_system,
    LogLevel,
    RefsList,
)

log = log_system.get_or_create_logger("user", LogLevel.INFO)


# ------------------------------------------------
# ITEM
# ------------------------------------------------
def can_modify_login(right_name: str, user: Item) -> bool:
    """Tel if the field "login" of the user can be modified

    :param right_name: The name of the right (here ="modify")
    :type right_name: str
    :param user: the user Item we want to modify login
    :type user: Item
    :return: True if current_user can modify the login
    :rtype: bool
    """
    if current_user.has_role(["ADMIN"]):
        return True
    return False


def can_modify_roles(right_name: str, user: Item) -> bool:
    """Tel if the roles field of the user can be modified

    :param right_name: The name of the right (here ="modify")
    :type right_name: str
    :param user: the user Item we want to modify roles
    :type user: Item
    :return: True if current_user can modify the roles field
    :rtype: bool
    """
    if current_user.has_role(["ADMIN"]):
        return True
    return False


# ------------------------------------
# Description of the Item
#
# The item is the object in the collection
# ------------------------------------
item = Item(
    {
        "login": String(require=True, can_modify=can_modify_login),
        "email": String(),
        "roles": List(
            String(union=["ADMIN", "EMPLOYEE", "USER"], default="USER"),
            can_modify=can_modify_roles,
        ),
        "rent": Dict({"books": RefsList(coll="books", field="$.borrow.user")}),
    }
)


# ------------------------------------------------
# COLLECTION
# ------------------------------------------------

# First define the connector  = where to store datas
connector = DBMongoConnector(
    connection_string="mongodb://localhost:27017/media_library", collection="Users"
)


def can_create(right_name: str, user: Item) -> bool:
    """Check if current_user can create a user


    :param right_name: The name of the right (here ="create")
    :type right_name: str
    :param user: the user Item we want to create
    :type user: Item
    :return: True if current_user can create this user
    :rtype: bool
    """

    log.debug(f"can create user by {current_user.login} ? ")

    if current_user.has_role("ADMIN"):
        return True

    # In this case, current_user.is_anonymous() is authorized to create a user
    # because anonymous user is used during auto creation in the login attempt
    # (if the user doesn't exist, he is created)
    if current_user.is_anonymous():
        return True
    return False


def can_read(right_name: str, user: Item) -> bool:
    """Check if current_user can read a user

    :param right_name: The name of the right (here ="read")
    :type right_name: str
    :param user: the user Item we want to read
    :type user: Item
    :return: True if current_user can read this user
    :rtype: bool
    """

    log.debug(f"can read user by {current_user.login} ? ")

    if current_user.has_role(["ADMIN", "EMPLOYEE"]):
        return True
    if user._id == current_user._id:
        return True

    # In this case, current_user.is_anonymous() is authorized to read a user
    # because anonymous user is used during auto creation in the login attempt
    # (must check if the user exist in the db before his creation)
    if current_user.is_anonymous():
        return True
    return False


def can_modify(right_name: str, user: Item) -> bool:
    """Check if current_user can modify a user"""

    log.debug(f"can modify user by {current_user.login} ? ")

    if current_user.has_role(["ADMIN", "EMPLOYEE"]):
        return True

    # I can modify myself
    if user._id == current_user._id:
        return True
    return False


def can_delete(right_name: str, user: Item) -> bool:
    """Check if current_user can delete a user"""

    log.debug(f"can delete user by {current_user.login} ? ")

    if current_user.has_role("ADMIN"):
        return True

    # auto_deletion is possible
    if user._id == current_user._id:
        return True

    return False


#
# The collection creation
#
# Association of Item, collector, rights
#
users = Collection(
    "users",
    item,
    connector,
    can_read=can_read,
    can_create=can_create,
    can_modify=can_modify,
    can_delete=can_delete,
)


# ------------------------------------------------
# ACTIONS
#
# Actions are a specific fuction with parameters we apply on an Item
# ------------------------------------------------
def toggle_role(action: Action, user: Item) -> None:
    """Change roles for a user

    :param action: The action object
    :type action: Action
    :param user: The user to apply the action
    :type user: Item
    """
    if action.role in user.roles:
        user.roles.remove(action.role)
    else:
        user.roles.append(action.role)
    # Save into the DB
    user.save()


def can_toggle_role(right_name: str, user: Item) -> bool:
    """check if current_user can execute or see this action

    :param right_name: The name of the right (here ="execute" or "see" )
    :type right_name: str
    :param user: the user on wich we want to see or execute the action
    :type user: Item
    :return: True if current_user can execute or see the action on this user
    :rtype: bool
    """
    if current_user.has_role("ADMIN"):
        return True
    return False


#
# Definition of the action
add_role_action = Action(
    {"role": String(union=["ADMIN", "EMPLOYEE", "USER"], default="USER")},
    toggle_role,
    can_execute=can_toggle_role,
    can_see=can_toggle_role,
)

# Add the action to the users collection
users.register_action("toggle_role", add_role_action)


# ------------------------------------------------
# SELECTIONS
#
# soon
# ------------------------------------------------
