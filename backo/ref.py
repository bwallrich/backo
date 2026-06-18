"""
Ref and RefsLink class definition
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code, logging-fstring-interpolation

import sys
import copy

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import String, Selector, SSyntaxError, STypeError, Kparse

from .loop_path import LoopPath
from .error import PathNotFoundError
from .log import log_system, LogLevel

# WARNING: Specific import for cycling import beetween Ref and RefsLists
from . import refslist

log = log_system.get_or_create_logger("ref", LogLevel.DEBUG)

DEFAULT_ID = "NULL_ID"


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


REF_KPARSE_MODEL = {
    "collection|coll*": str,
    "reverse|rev|field": str,
    "require|required": {"type": bool, "default": False},
    "on": {"type": list[tuple], "default": []},
}


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

        options = Kparse(kwargs, REF_KPARSE_MODEL)

        self._collection = options.get("collection")
        self._reverse = options.get("reverse")
        self._coll_ref = None

        # For required
        require = options.get("require")
        default = DEFAULT_ID if require is True else None

        # for events
        on = copy.copy(options.get("on"))
        on.append(("created", self.on_created, "$"))
        on.append(("before_delete", self.on_delete, "$"))
        on.append(("before_save", self.on_before_save, "$"))
        on.append(("check_syntax", self.check_syntax, "$"))

        String.__init__(
            self,
            default=default,
            required=require,
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
            raise SSyntaxError(
                'Ref "{0}" to unnknown collection "{1}"',
                self.path_name(),
                self._collection,
            )

        return

    def get_schema(self) -> dict:
        """get schema for ref with specific elements
        collection and reverse

        :return: the schema
        :rtype: dict
        """
        a = super().get_schema()
        a["collection"] = self._collection
        a["reverse"] = self._reverse
        return a

    def check_syntax(
        self, event_name: str, root, me, **kwargs
    ):  # pylint: disable=unused-argument
        """
        Check if everything is correct log some warnings
        """
        log.debug(f"Check the syntax {me.path_name()}")

        try:
            me.set_collection_reference()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        if not me._coll_ref:
            log.error(
                f'{root._collection.name}/{me.path_name()}: Collection "{me._collection}" not found'
            )
            return

        if not me._reverse:
            log.warning(
                f'{root._collection.name}/{me.path_name()}: Collection "{me._collection}". No reverse defined. Are you sure ?'
            )
        else:
            # fill the field
            other = me._coll_ref.new_item()
            reverse_field = other.select(me._reverse)
            # Must check == None rather

            if not isinstance(
                reverse_field, (refslist.RefsList, Ref)
            ):  # pylint: disable=singleton-comparison
                log.error(
                    f'{root._collection.name}/{me.path_name()}: Collection "{me._collection}", "{me._reverse}" is not a Ref or a RefsList'
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

        log.debug(f"Ref on_create {id(me.get_root())} {id(root)} {me.path_name()}")

        if not me._reverse:
            return

        # A created object with no reference set. finish
        target_id = me.get_value()
        log.debug(f"Ref on_create {me.path_name()} {target_id}")

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
        # try:
        # except Exception as e:
        #     log.warning(f'{self.path_name()} : load {target_id} in collection {me._collection} return an error ({e})')
        #     return

        # fill the field
        reverse_field = other.select(me._reverse)

        if reverse_field is None:
            raise PathNotFoundError(
                'Path "{0}" not found in collection "{1}"',
                me._reverse,
                self._collection,
            )

        looper.append(root._collection.name, root._id.get_value(), me.path_name())

        # direct reference
        if isinstance(reverse_field, Ref):
            reverse_field.set(root._id)
            other.save(**kwargs)
            return

        # List of references, (fill only if refslist.FillStrategy.FILL)
        if isinstance(reverse_field, refslist.RefsList):
            if reverse_field._fill_strategy == refslist.FillStrategy.FILL:
                if root._id.get_value() not in reverse_field.get_value():
                    # update the reverse
                    log.debug(f"update reverse refList {me._reverse} with {root._id}")
                    reverse_field.append(root._id)
                    log.debug(f"update reverse refList {me._reverse} => {other}")
                    other.save(**kwargs)
            return

        # WTF
        raise STypeError(
            "{0}.{1} is not a Ref or a RefsList", self._collection, me._reverse
        )

    def on_delete(
        self, event_name, root, me, **kwargs
    ):  # pylint: disable=unused-argument, too-many-return-statements
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
        try:
            other.load(me.get_value())
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.warning(
                f"{self.path_name()} : load {me.get_value()} in collection {me._collection} return an error ({e})"
            )
            return

        # fill the field
        reverse_field = other.select(me._reverse)
        if reverse_field is None:
            raise PathNotFoundError(
                'Path "{0}" not found in collection "{1}"',
                me._reverse,
                self._collection,
            )

        looper.append(root._collection.name, root._id.get_value(), me.path_name())

        # direct reference
        if isinstance(reverse_field, Ref):
            if reverse_field == root._id:
                reverse_field.set(None)
                other.save(**kwargs)
            return

        # List of references
        if isinstance(reverse_field, refslist.RefsList):
            if reverse_field._fill_strategy == refslist.FillStrategy.FILL:
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

        raise STypeError(
            "{0}.{1} is not a Ref or a RefsList", self._collection, me._reverse
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
        except Exception:  # pylint: disable=broad-exception-caught
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
