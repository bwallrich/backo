"""
Ref and RefsLink class definition
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code, logging-fstring-interpolation

import sys
import logging
import re
from enum import Enum, auto

sys.path.insert(1, "../../stricto")
from stricto import String, List

from .error import Error, ErrorType
from .log import log_system


log = log_system.get_or_create_logger("ref", logging.DEBUG)

DEFAULT_ID = "NULL_ID"


class DeleteStrategy(Enum):
    """
    Specifics strategy for deletion for Refs
    """

    MUST_BE_EMPTY = auto()
    DELETE_REFERENCED_ITEMS = auto()
    UNLINK_REFERENCED_ITEMS = auto()

    def __repr__(self):
        return self.name


class FillStrategy(Enum):
    """
    Specifics strategy for fill RefsList in case of one_to_many or many_to_many links

    FILL : The reverse is a List of _ids. Usefull to manage which is pointing to me.
    NOT_FILL : Whe don't want to fill because the list is to big (for example person -> nationality)
    but is important to keep the information of this link.
    """

    FILL = auto()  # The default
    NOT_FILL = auto()

    def __repr__(self):
        return self.name


class Ref(String):  # pylint: disable=too-many-instance-attributes
    """

    ██████╗ ███████╗███████╗
    ██╔══██╗██╔════╝██╔════╝
    ██████╔╝█████╗  █████╗
    ██╔══██╗██╔══╝  ██╔══╝
    ██║  ██║███████╗██║
    ╚═╝  ╚═╝╚══════╝╚═╝

    A reference to another table
    """

    def __init__(self, **kwargs):
        """
        available arguments
        """
        self._collection = kwargs.pop(
            "collection", kwargs.pop("coll", kwargs.pop("table", None))
        )
        self._reverse = kwargs.pop(
            "reverse", kwargs.pop("rev", kwargs.pop("field", None))
        )
        self._coll_ref = None

        # For required
        not_none = kwargs.pop("notNone", kwargs.pop("required", False))
        default = DEFAULT_ID if not_none is True else None

        # for events
        on = kwargs.pop("on", [])
        on.append(("created", self.on_created))
        on.append(("before_delete", self.on_delete))
        on.append(("before_save", self.on_before_save))

        String.__init__(
            self,
            default=default,
            required=not_none,
            on=on,
            **kwargs,
        )

    def set_collection_reference(self):
        """
        Set the reference to the Item object to the collection referenced.
        """
        # Already set
        if self._coll_ref is not None:
            return

        root1 = self.get_root()._collection
        self._coll_ref = root1.get_other_collection(self._collection)
        if not self._coll_ref:
            raise Error(
                ErrorType.COLLECTION_NOT_FOUND,
                f'Collection "{self._collection}" not found',
            )
        return

    def on_before_save(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Before saving, check if the reference
        as changed from an old value
        """
        log.debug(
            "%r/%r save. Check for changes in Ref %r",
            root._collection.name,
            root._id,
            me.path_name(),
        )

        # loop in references modifications
        path_to_find = (
            "from",
            root._collection.name,
            root._id.get_value(),
            me.path_name(),
        )

        if path_to_find in kwargs.get("m_path", []):
            log.debug(
                "Stop following ref due to loop found for %r in %r",
                path_to_find,
                kwargs.get("m_path", []),
            )
            return

        if len(kwargs.get("m_path", [])) > 4:
            raise Error(
                ErrorType.FIELD_NOT_FOUND,
                f"on_change - LOOP {path_to_find} in {kwargs.get('m_path', [])}",
            )

        # get the old object. If not, the object is currently creating
        old = kwargs.get("old_object")
        if old is None:
            return

        # get the previous version of "me" and check if there is a version
        # and different from the new one
        old_me = old.select(me.path_name())
        if old_me == me:
            return

        log.debug(
            "%r/%r %r change %r->%r",
            root._collection.name,
            root._id,
            me.path_name(),
            old_me,
            me,
        )

        if old_me.get_value() is not None:
            self.on_delete(event_name, root, old_me, **kwargs)
        if me.get_value() is not None:
            self.on_created(event_name, root, me, **kwargs)

    def on_created(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The object as been created
        check for the reverse field and modify it
        """
        log.debug(
            "Creation %r/%r.%r=%r ", root._collection.name, root._id, me.path_name(), me
        )

        if not me._reverse:
            return

        target_id = me.get_value()
        if target_id is None:
            return

        path = ("from", root._collection.name, root._id.get_value(), me.path_name())

        # set the _coll_ref (in case of)
        me.set_collection_reference()
        # try to load the coresponding field
        other = me._coll_ref.new()
        other.load(target_id)

        # fill the field
        reverse_field = other.select(me._reverse)
        if reverse_field is None:
            raise Error(
                ErrorType.FIELD_NOT_FOUND,
                f'Collection "{self._collection}"."{me._reverse}" not found',
            )

        # direct reference
        if isinstance(reverse_field, Ref):
            if path not in kwargs["m_path"]:
                kwargs["m_path"].append(path)

            reverse_field.set(root._id)
            other.save(**kwargs)
            return

        # List of references
        if isinstance(reverse_field, RefsList):
            if root._id.get_value() not in reverse_field.get_value():
                if path not in kwargs["m_path"]:
                    kwargs["m_path"].append(path)

                reverse_field.append(root._id)
                other.save(**kwargs)
            return

        # WTF
        raise Error(
            ErrorType.NOT_A_REF,
            # pylint: disable=line-too-long
            f'Collection "{self._collection}"."{me._reverse}" "{type(reverse_field)}" is not a Ref or a RefsList',
        )

    def on_delete(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The object will be deleted
        clean structure
        """

        if not me._reverse:
            log.debug("%r has no reverse ?", me)
            return

        if me == DEFAULT_ID:
            return

        # check if in a loop on m_path
        if (event_name, me._reverse, me.get_value()) in kwargs.get("m_path", []):
            return

        log.debug(
            "Delete %r/%r %r=%r ", root._collection.name, root._id, me.path_name(), me
        )

        # set the _coll_ref (in case of)
        me.set_collection_reference()
        # try to load the coresponding field
        other = me._coll_ref.new()
        other.load(me.get_value())

        # fill the field
        reverse_field = other.select(me._reverse)
        if reverse_field is None:
            raise Error(
                ErrorType.FIELD_NOT_FOUND,
                f'Collection "{self._collection}"."{me._reverse}" not found',
            )

        # direct reference
        if isinstance(reverse_field, Ref):
            if reverse_field == root._id:
                reverse_field.set(None)
                path = (
                    "from",
                    root._collection.name,
                    root._id.get_value(),
                    me.path_name(),
                )
                if path not in kwargs["m_path"]:
                    kwargs["m_path"].append(path)

                other.save(**kwargs)
            return

        # List of references
        if isinstance(reverse_field, RefsList):

            log.debug(
                "Ref on_delete clean refList %r %r %r", me._collection, me._reverse, me
            )

            if root._id.get_value() in reverse_field.get_value():
                reverse_field.remove(root._id.get_value())
                path = (
                    "from",
                    root._collection.name,
                    root._id.get_value(),
                    me.path_name(),
                )
                if path not in kwargs["m_path"]:
                    kwargs["m_path"].append(path)

                other.save(**kwargs)
            return

        raise Error(
            ErrorType.NOT_A_REF,
            f'Collection "{self._collection}"."{me._reverse}" is not a Ref or a RefsList',
        )

    def get_selectors(self, sel_filter, selectors_as_list):
        """
        rewrite get_selector to populate the sub-object and continue
        """
        # Return the _id itself
        if not selectors_as_list:
            return String.get_selectors(self, sel_filter, selectors_as_list)

        # Load the other to continue

        # set the _coll_ref (in case of)
        self.set_collection_reference()
        # try to load the coresponding field
        other = self._coll_ref.new()
        try:
            other.load(self.get_value())
        except Error:
            pass
        return other.get_selectors(sel_filter, selectors_as_list)

    def get_view(self, view_name, final=True):  # pylint: disable=protected-access
        """
        Return all elements belonging to view_name
        tue return is a subset of this Dict
        """
        return String.get_view(self, view_name, final)


class RefsList(List):
    """

    ██████╗ ███████╗███████╗███████╗██╗     ██╗███████╗████████╗
    ██╔══██╗██╔════╝██╔════╝██╔════╝██║     ██║██╔════╝╚══██╔══╝
    ██████╔╝█████╗  █████╗  ███████╗██║     ██║███████╗   ██║
    ██╔══██╗██╔══╝  ██╔══╝  ╚════██║██║     ██║╚════██║   ██║
    ██║  ██║███████╗██║     ███████║███████╗██║███████║   ██║
    ╚═╝  ╚═╝╚══════╝╚═╝     ╚══════╝╚══════╝╚═╝╚══════╝   ╚═╝
    A list of reference to another table
    """

    def __init__(self, **kwargs):
        r"""Fetches and returns this thing

        :param first:
            The first parameter
        :type first: ``int``
        :param second:
            The second parameter
        :type second: ``str``
        :param \**kwargs:
            See below
             :Keyword Arguments:
            * *extra* (``list``) --
              Extra stuff
            * *supplement* (``dict``) --
              Additional content

        """
        self._collection = kwargs.pop(
            "collection", kwargs.pop("coll", kwargs.pop("table", None))
        )
        self._reverse = kwargs.pop(
            "reverse", kwargs.pop("rev", kwargs.pop("field", None))
        )
        self._require = kwargs.pop("require", True)
        self._coll_ref = None

        # Strategy for fill
        self._fill_strategy = kwargs.pop(
            "ofs", kwargs.pop("on_fill", FillStrategy.FILL)
        )
        if self._fill_strategy != FillStrategy.FILL:
            self._fill_strategy = FillStrategy.NOT_FILL

        # Strategy for deletion and modification
        on_modify_strategy = None
        on_delete_strategy = kwargs.pop(
            "ods", kwargs.pop("on_delete", DeleteStrategy.MUST_BE_EMPTY)
        )
        if on_delete_strategy == DeleteStrategy.MUST_BE_EMPTY:
            on_delete_strategy = self.on_delete_must_by_empty
        if on_delete_strategy == DeleteStrategy.DELETE_REFERENCED_ITEMS:
            on_delete_strategy = self.on_delete_with_reverse
        if on_delete_strategy == DeleteStrategy.UNLINK_REFERENCED_ITEMS:
            on_delete_strategy = self.on_delete_clean_reverse

        on_modify_strategy = self.on_modify_clean_reverse

        # for events
        on = kwargs.pop("on", [])
        on.append(("created", self.on_created))
        on.append(("before_delete", on_delete_strategy))
        on.append(("before_save", on_modify_strategy))

        List.__init__(
            self, String(default=DEFAULT_ID, required=True), on=on, default=[], **kwargs
        )

    def set_collection_reference(self):
        """
        Set the reference to the Item object to the collection referenced.
        """
        # Already set
        if self._coll_ref is not None:
            return

        root1 = self.get_root()._collection
        self._coll_ref = root1.get_other_collection(self._collection)
        if not self._coll_ref:
            raise Error(
                ErrorType.COLLECTION_NOT_FOUND,
                f'Collection "{self._collection}" not found',
            )
        return

    def on_delete_must_by_empty(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The object will be deleted only if this list is empty
        otherwist error
        """
        log.debug(
            "%r/%r deleted with RefsList %r=%r and must be empty",
            root._collection.name,
            root._id,
            me.path_name(),
            me,
        )
        # With fill strategy, just chek if the list is empty
        if self._fill_strategy == FillStrategy.FILL:
            if len(me) != 0:
                raise Error(
                    ErrorType.REFSLIST_NOT_EMPTY,
                    f'Collection "{self._collection}" not empty',
                )

        # With not fill strategy, must select all where target_id is me
        # and check if we find them
        # To do : implement strategy NO_FILL
        # if self._fill_strategy == FillStrategy.NOT_FILL:
        #    return

    def on_delete_with_reverse(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The ref object object will be deleted too
        otherwist error
        """
        log.debug(
            "%r/%r deleted with RefsList %r=%r and delete reverses too",
            root._collection.name,
            root._id,
            me.path_name(),
            me,
        )

        # set the _coll_ref (in case of)
        me.set_collection_reference()

        # try to load the coresponding field
        for reference in me:
            other = me._coll_ref.new()
            other.load(reference.get_value(), **kwargs)
            path = ("from", root._collection.name, root._id.get_value(), me.path_name())
            if path not in kwargs["m_path"]:
                kwargs["m_path"].append(path)
            other.delete(**kwargs)

    def on_delete_clean_reverse(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The reflecting object is cleaned too
        """
        log.debug(
            "%r/%r deleted with RefsList %r=%r and clean reverses",
            root._collection.name,
            root._id,
            me.path_name(),
            me,
        )
        return self.change_others_ref_to(root, me, me, None, **kwargs)

    def change_others_ref_to(self, root, me, list_of_refs, new_ref, **kwargs):
        """
        factorisation
        root : The root
        me   : the currente RefList
        list_of_refs : an Array of Ref to set to new_ref
        new_ref : the new reverence (can be None)
        """

        # set the _coll_ref (in case of)
        me.set_collection_reference()

        # loop in references modifications
        path_to_find = (
            "from",
            root._collection.name,
            root._id.get_value(),
            me.path_name(),
        )
        if path_to_find in kwargs.get("m_path", []):
            log.debug(
                "Stop following ref due to loop found for %r in %r",
                path_to_find,
                kwargs.get("m_path", []),
            )
            return

        if len(kwargs.get("m_path", [])) > 4:
            raise Error(
                ErrorType.FIELD_NOT_FOUND,
                f"on_change + LOOP {path_to_find} in {kwargs.get('m_path', [])}",
            )

        # Change the correspondant field to the new one
        for reference in list_of_refs:
            other = me._coll_ref.new()
            other.load(reference.get_value(), **kwargs)

            reverse_field = other.select(me._reverse)
            if reverse_field is None:
                raise Error(
                    ErrorType.FIELD_NOT_FOUND,
                    f'Collection "{self._collection}"."{me._reverse}" not found',
                )

            if not isinstance(reverse_field, (Ref, RefsList)):
                raise Error(
                    ErrorType.NOT_A_REF,
                    f'Collection "{self._collection}"."{me._reverse}" is not a Ref or a RefsList',
                )

            path_to_find = (
                "from",
                other._collection.name,
                reference.get_value(),
                reverse_field.path_name(),
            )
            if path_to_find in kwargs.get("m_path", []):
                log.debug(
                    "Ignore following ref due to loop found for %r in %r",
                    path_to_find,
                    kwargs.get("m_path", []),
                )
                continue

            other_modified_flag = False

            if isinstance(reverse_field, Ref):
                # The reverse field is a Ref, modify it
                log.debug(
                    "Change Ref %r/%r.%r -> %r",
                    me._collection,
                    reference,
                    me._reverse,
                    new_ref,
                )

                reverse_field.set(new_ref)
                other_modified_flag = True
            else:
                # the reverse field is a refsList.
                # Append to the new one if not exists or clean if None
                if new_ref is None:
                    if root._id in reverse_field:
                        log.debug(
                            "RefsList %r/%r.%r=%r remove %r",
                            me._collection,
                            reference,
                            me._reverse,
                            reverse_field,
                            root._id,
                        )
                        reverse_field.remove(root._id)
                        other_modified_flag = True
                else:
                    if new_ref not in reverse_field:
                        log.debug(
                            "%r/%r.%r=%r add %r",
                            me._collection,
                            reference,
                            me._reverse,
                            reverse_field,
                            new_ref,
                        )
                        reverse_field.append(new_ref)
                        other_modified_flag = True

            if other_modified_flag:
                path = (
                    "from",
                    root._collection.name,
                    root._id.get_value(),
                    me.path_name(),
                )
                if path not in kwargs["m_path"]:
                    kwargs["m_path"].append(path)
                other.save(**kwargs)

    def on_created(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        A creation object with reflists
        """
        log.debug(
            "%r/%r created with RefsList %r=%r",
            root._collection.name,
            root._id,
            me.path_name(),
            me,
        )
        if me:
            self.change_others_ref_to(root, me, me, root._id, **kwargs)

    def on_modify_clean_reverse(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The reflecting object is set to the new one
        """
        # get the olf object
        old = kwargs.get("old_object")
        if old is None:
            return

        # get the previous version of "me" and check if there is a version
        # and different from the new one
        old_me = old.select(me.path_name())

        log.debug(
            "%r/%r change %r=%r->%r",
            root._collection.name,
            root._id,
            me.path_name(),
            old_me,
            me,
        )

        # set the _coll_ref (in case of)
        me.set_collection_reference()

        # modify ref to me to the new one
        l = []
        for reference in me:
            if reference.get_value() not in old_me:
                l.append(reference)
        if l:
            log.debug(
                f"Must change {me._collection}/{me._reverse} for {l} to {root._id}"
            )
            self.change_others_ref_to(root, me, l, root._id, **kwargs)

        # modify ref to None to those who disapear
        l = []
        for reference in old_me:
            if reference.get_value() not in me:
                l.append(reference)
        if l:
            log.debug(f"Must change {me._collection}/{me._reverse} for {l} to {None}")
            self.change_others_ref_to(root, me, l, None, **kwargs)

    def get_selectors(self, sel_filter, selectors_as_list):
        """
        rewrite get_selector to populate the sub-object and continue
        """
        # Return the _id itself
        if not selectors_as_list:
            return String.get_selectors(self, sel_filter, selectors_as_list)

        # Load others to continue

        # set the _coll_ref (in case of)
        self.set_collection_reference()
        # try to load the coresponding field

        if sel_filter is None:
            a = []
            for v in self._value:
                other = self._coll_ref.new()
                other.load(v)
                if not other:
                    continue
                result = other.get_selectors(None, selectors_as_list.copy())
                if result is not None:
                    a.append(result)
            return a

        if re.match("^-*[0-9]+$", sel_filter):
            try:
                v = self._value[int(sel_filter)]
            except IndexError:
                return None
            other = self._coll_ref.new()
            other.load(v)
            if other:
                return other.get_selectors(None, selectors_as_list)

        return None
