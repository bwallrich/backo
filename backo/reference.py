"""
Ref and RefsLink class definition
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code, logging-fstring-interpolation

import sys
import re
from enum import Enum, auto
from typing import Self

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import String, List, Selector, Dict

from .loop_path import LoopPath
from .error import Error, ErrorType
from .log import log_system, LogLevel
from .api_toolbox import append_path_to_filter


log = log_system.get_or_create_logger("ref", LogLevel.INFO)

DEFAULT_ID = "NULL_ID"


class DeleteStrategy(Enum):
    """
    Specifics strategy for deletion for :py:class:`RefsList`

    when the user want to delete the object, if the object contains a :py:class:`RefsList`. Say how to handle the deletion

        - ``MUST_BE_EMPTY`` = The RefsList must be empty otherwise the delete action will raise an error.
        - ``DELETE_REFERENCED_ITEMS`` = All objects targeted with this RefsList will be deleted too. Caution !
        - ``UNLINK_REFERENCED_ITEMS`` = The reverse field of all objects targeted with this RefsList will be cleaned

    """

    MUST_BE_EMPTY = auto()
    DELETE_REFERENCED_ITEMS = auto()
    UNLINK_REFERENCED_ITEMS = auto()

    def __repr__(self):
        return self.name


class FillStrategy(Enum):
    """
    Specifics strategy for fill RefsList in case of one_to_many or many_to_many links

    - ``FILL`` = The reverse is a List of _ids. Usefull to manage which is pointing to me.
    - ``NOT_FILL`` = Whe don't want to fill because the list is to big (for example person -> nationality) but is important to keep the information of this link.

    """

    FILL = auto()  # The default
    NOT_FILL = auto()

    def __repr__(self):
        return self.name


# pylint: disable=pointless-string-statement
"""
██████╗ ███████╗███████╗
██╔══██╗██╔════╝██╔════╝
██████╔╝█████╗  █████╗
██╔══██╗██╔══╝  ██╔══╝
██║  ██║███████╗██║
╚═╝  ╚═╝╚══════╝╚═╝
A reference to another table
"""


class Ref(String):  # pylint: disable=too-many-instance-attributes
    """Ref 0 or 1 to many to another :py:class:`Collection`

    :param ``**kwargs``:
        - *collection|coll=* ``str`` -- The target collection
        - *reverse|rev|field=* ``str`` -- The field in the target collection which reference my collection. Must be a RFC 9535 path (https://datatracker.ietf.org/doc/rfc9535/)


    .. code-block:: python

        from backo import Item, Ref, RefsList

        # example
        book_item = Item({
            "title": String(),
            "author": Ref(collection="authors", field="$.books", required=True),
        })
        author_item = Item({
            "name": String(),
            "surname": String(),
            "books": RefsList(collection="books", field="$.author"),
        })

        books = Collection( "books", book_item, database_for_books )
        authors = Collection( "authors", author_item, database_for_authors )

        my_bookstore = Backoffice("bookstore")
        my_bookstore.register_collection(books)
        my_bookstore.register_collection(authors)


    """

    def __init__(self, **kwargs):
        """Constructor"""
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
        """Set the reference to the Item object to the collection referenced.

        :meta private:

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

        :meta private:

        """
        # No reverse => nothing to do.
        if not me._reverse:
            return

        # get the old object. If not, the object is currently creating
        old = kwargs.get("old_object")
        if old is None:
            return

        # get the previous version of "me" and check if there is a version
        # and different from the new one
        old_me = old.select(me.path_name())
        if old_me == me:
            return

        # Get looper or create it
        if "looper" not in kwargs:
            kwargs["looper"] = LoopPath()
        looper: LoopPath = kwargs.get("looper")

        log.debug(
            "%r/%r save. Check for changes in Ref %r",
            root._collection.name,
            root._id,
            me.path_name(),
        )

        if looper.is_loop(root._collection.name, root._id.get_value(), me.path_name()):
            log.debug(
                f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
            )
            return
        looper.append(root._collection.name, root._id.get_value(), me.path_name())

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

        :meta private:

        """
        # No reverse => nothing to do.
        if not me._reverse:
            return

        # A created object with no reference set. finish
        target_id = me.get_value()
        if target_id is None:
            return

        # Get looper or create it
        if "looper" not in kwargs:
            kwargs["looper"] = LoopPath()
        looper: LoopPath = kwargs.get("looper")

        log.debug(
            "Creation %r/%r.%r=%r ", root._collection.name, root._id, me.path_name(), me
        )

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

        looper.append(root._collection.name, root._id.get_value(), me.path_name())

        # direct reference
        if isinstance(reverse_field, Ref):
            reverse_field.set(root._id)
            other.save(**kwargs)
            return

        # List of references, (fill only if FillStrategy.FILL)
        if isinstance(reverse_field, RefsList):
            if reverse_field._fill_strategy == FillStrategy.FILL:
                if root._id.get_value() not in reverse_field.get_value():

                    # update the reverse
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

        :meta private:

        """
        # No reverse => nothing to do.
        if not me._reverse:
            return

        # Get looper or create it
        if "looper" not in kwargs:
            kwargs["looper"] = LoopPath()
        looper: LoopPath = kwargs.get("looper")

        if me == DEFAULT_ID:
            return

        # if me.get_value() == None:
        if me.get_value() is None:
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

        looper.append(root._collection.name, root._id.get_value(), me.path_name())

        # direct reference
        if isinstance(reverse_field, Ref):
            if reverse_field == root._id:
                reverse_field.set(None)
                other.save(**kwargs)
            return

        # List of references
        if isinstance(reverse_field, RefsList):
            if reverse_field._fill_strategy == FillStrategy.FILL:
                log.debug(
                    "Ref on_delete clean refList %r %r %r",
                    me._collection,
                    me._reverse,
                    me,
                )

                if root._id.get_value() in reverse_field.get_value():
                    reverse_field.remove(root._id.get_value())
                    other.save(**kwargs)
            return

        raise Error(
            ErrorType.NOT_A_REF,
            f'Collection "{self._collection}"."{me._reverse}" is not a Ref or a RefsList',
        )

    def get_selectors(self, index_or_slice, sel: Selector):
        """
        rewrite get_selector to populate the sub-object and continue

        :meta private:

        """
        # Cannot have index or slice on a Ref
        if index_or_slice:
            return None

        if sel.empty():
            return self

        # Load the other to continue

        # set the _coll_ref (in case of)
        self.set_collection_reference()
        # try to load the coresponding field
        other = self._coll_ref.new()
        try:
            other.load(self.get_value())
        except Error:
            pass

        # The index_or_slice is actually ignored.
        # (key, sub_index_or_slice) = sel.pop()

        # continue the selection
        return other.get_selectors(None, sel)

    def get_view(self, view_name, final=True):  # pylint: disable=protected-access
        """
        Return all elements belonging to view_name
        true return is a subset of this Dict

        :meta private:

        """
        return String.get_view(self, view_name, final)


"""
██████╗ ███████╗███████╗███████╗██╗     ██╗███████╗████████╗
██╔══██╗██╔════╝██╔════╝██╔════╝██║     ██║██╔════╝╚══██╔══╝
██████╔╝█████╗  █████╗  ███████╗██║     ██║███████╗   ██║
██╔══██╗██╔══╝  ██╔══╝  ╚════██║██║     ██║╚════██║   ██║
██║  ██║███████╗██║     ███████║███████╗██║███████║   ██║
╚═╝  ╚═╝╚══════╝╚═╝     ╚══════╝╚══════╝╚═╝╚══════╝   ╚═╝
A list of reference to another table
"""


class RefsList(List):
    """Ref 0 or 1 to many to another :py:class:`Collection`

    :param ``**kwargs``:
        - *collection|coll=* ``str`` -- The target collection
        - *reverse|rev|field=* ``str`` -- The field in the target collection which reference my collection. Must be a RFC 9535 path (https://datatracker.ietf.org/doc/rfc9535/)
        - *on_delete|ods=* :py:class:`DeleteStrategy` -- The deletion strategy :py:class:`DeleteStrategy`. By default =``DeleteStrategy.MUST_BE_EMPTY``

    .. code-block:: python

        from backo import Item, Ref, RefsList, DeleteStrategy

        # example
        book_item = Item({
            "title": String(),
            "author": Ref(collection="authors", field="$.books", required=True),
        })
        author_item = Item({
            "name": String(),
            "surname": String(),
            "books": RefsList(collection="books", field="$.author", ods=DeleteStrategy.DELETE_REFERENCED_ITEMS),
        })

        books = Collection( "books", book_item, database_for_books )
        authors = Collection( "authors", author_item, database_for_authors )

        my_bookstore = Backoffice("bookstore")
        my_bookstore.register_collection(books)
        my_bookstore.register_collection(authors)


    """

    def __init__(self, **kwargs):
        """Constructor"""
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
        """Set the reference to the Item object to the collection referenced.

        :meta private:

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

    def get_other_with_a_select(self, root_id: str) -> list:
        """Get reverse Items with a select
        (when FillStrategy.NO_FILL)

        :return: list of Items
        :rtype: list
        """
        # No reverse => nothing to do.
        if not self._reverse:
            return []

        self.set_collection_reference()
        reverse_field = self._coll_ref.model.select(self._reverse)
        reverse_field = self._coll_ref.model.select(self._reverse)
        if not isinstance(reverse_field, (Ref, RefsList)):
            raise Error(
                ErrorType.NOT_A_REF,
                f'Collection "{self._collection}"."{self._reverse}" is not a Ref or a RefsList',
            )

        match_filter = {}
        if isinstance(reverse_field, Ref):
            append_path_to_filter(
                match_filter,
                re.sub(r"^\$\.", "", self._reverse),
                [root_id],
            )
        if isinstance(reverse_field, RefsList):
            append_path_to_filter(
                match_filter,
                re.sub(r"^\$\.", "", self._reverse),
                ("$contains", root_id),
            )
        return self._coll_ref.select(match_filter)

    def on_delete_must_by_empty(
        self, event_name: str, root: Dict, me: Self, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The object will be deleted only if this list is empty
        otherwist error

        :meta private:

        """

        log.debug(
            "%r/%r deleted with RefsList %r=%r and must be empty",
            root._collection.name,
            root._id,
            me.path_name(),
            me,
        )
        # With FillStrategy.FILL, just chek if the list is empty
        if self._fill_strategy == FillStrategy.FILL:
            if len(me) != 0:
                raise Error(
                    ErrorType.REFSLIST_NOT_EMPTY,
                    f'Collection "{self._collection}" not empty',
                )
        else:
            # FillStrategy.NOT_FILL, mus do a select to find
            # if ther is some ref to me.
            # set the _coll_ref (in case of)
            other_list = me.get_other_with_a_select(root._id.get_value())
            if len(other_list) != 0:
                raise Error(
                    ErrorType.REFSLIST_NOT_EMPTY,
                    f'Collection (not filled) "{self._collection}" not empty',
                )

    def on_delete_with_reverse(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The ref object object will be deleted too
        otherwist error

        :meta private:

        """

        # Get looper or create it
        if "looper" not in kwargs:
            kwargs["looper"] = LoopPath()
        looper: LoopPath = kwargs.get("looper")

        log.debug(
            "%r/%r deleted with RefsList %r=%r and delete reverses too",
            root._collection.name,
            root._id,
            me.path_name(),
            me,
        )

        # set the _coll_ref (in case of)
        me.set_collection_reference()

        looper.append(root._collection.name, root._id.get_value(), me.path_name())
        # With FillStrategy.FILL, try to delete the corresponding field
        if self._fill_strategy == FillStrategy.FILL:
            # try to load the coresponding field
            for reference in me:
                other = me._coll_ref.new()
                other.load(reference.get_value(), **kwargs)
                other.delete(**kwargs)
        else:
            # with FillStrategy.NO_FILL select all for deletion
            other_list = me.get_other_with_a_select(root._id.get_value())
            for other in other_list:
                other.delete(**kwargs)

    def on_delete_clean_reverse(
        self, event_name: str, root: Dict, me: Self, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The reflecting object is cleaned too

        :meta private:

        """

        log.debug(
            "%r/%r deleted with RefsList %r=%r and clean reverses",
            root._collection.name,
            root._id,
            me.path_name(),
            me,
        )

        if self._fill_strategy == FillStrategy.FILL:
            return self._change_others_ref_to(root, me, me, None, **kwargs)

        ## self._fill_strategy == FillStrategy.NO_FILL
        # with FillStrategy.NO_FILL select all for clean
        other_list = me.get_other_with_a_select(root._id.get_value())

        return self._change_others_ref_to(root, me, other_list, None, **kwargs)

    def _change_others_ref_to(
        self,
        root: Dict,
        me: Self,
        list_of_refs: Self | list[Ref],
        new_ref: str | None,
        **kwargs,
    ):
        """
        factorisation
        root : The root
        me   : the currente RefList
        list_of_refs : an Array of Ref to set to new_ref
        new_ref : the new reverence (can be None)

        :meta private:

        """
        # Get looper or create it
        if "looper" not in kwargs:
            kwargs["looper"] = LoopPath()
        looper: LoopPath = kwargs.get("looper")

        # set the _coll_ref (in case of)
        me.set_collection_reference()

        if looper.is_loop(root._collection.name, root._id.get_value(), me.path_name()):
            log.debug(
                f"Stop following ref due to loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
            )
            return
        looper.append(root._collection.name, root._id.get_value(), me.path_name())

        # if len(kwargs.get("m_path", [])) > 4:
        #     raise Error(
        #         ErrorType.FIELD_NOT_FOUND,
        #         f"on_change + LOOP {path_to_find} in {kwargs.get('m_path', [])}",
        #     )

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

            if looper.is_loop(
                other._collection.name, reference.get_value(), reverse_field.path_name()
            ):
                log.debug(
                    f"Ignore following ref due to fucking loop ( {root._collection.name}, {root._id.get_value()}, {me.path_name()})"
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
                other.save(**kwargs)

    def on_created(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        A creation object with a RefList
        Fill other if

        :meta private:

        """
        log.debug(
            "%r/%r created with RefsList %r=%r",
            root._collection.name,
            root._id,
            me.path_name(),
            me,
        )
        if me:
            self._change_others_ref_to(root, me, me, root._id, **kwargs)

    def on_modify_clean_reverse(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        The reflecting object is set to the new one

        :meta private:

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
            self._change_others_ref_to(root, me, l, root._id, **kwargs)

        # modify ref to None to those who disapear
        l = []
        for reference in old_me:
            if reference.get_value() not in me:
                l.append(reference)
        if l:
            log.debug(f"Must change {me._collection}/{me._reverse} for {l} to {None}")
            self._change_others_ref_to(root, me, l, None, **kwargs)

    def get_selectors(self, index_or_slice, sel: Selector):
        """
        rewrite get_selector to populate the sub-object and continue

        :meta private:

        """

        # No need to continue, return self or slice of lists
        if sel.empty():
            if index_or_slice is None:
                return self
            return List.get_selectors(self, index_or_slice, sel)

        # Get all ids depending on index_or_slice
        list_ids_or_id = List.get_selectors(self, index_or_slice, Selector(None))

        if list_ids_or_id is None:
            return None

        # set the _coll_ref (in case of)
        self.set_collection_reference()

        # Continue further with a list of ids
        if isinstance(list_ids_or_id, (RefsList, list, List)):
            a = []
            for other_id in list_ids_or_id:
                other = self._coll_ref.new()
                try:
                    other.load(other_id)
                except Error:
                    continue
                result = other.get_selectors(None, sel.copy())
                if result is not None:
                    a.append(result)
            return a

        # Continue further with a uniq id
        other = self._coll_ref.new()
        try:
            other.load(list_ids_or_id)
        except Error:
            return None
        return other.get_selectors(None, sel)
