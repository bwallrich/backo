"""
Ref and RefsLink class definition
"""
# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, duplicate-code

import sys
sys.path.insert(1, "../../stricto")

from stricto import String, List
from enum import Enum, auto
from .error import Error, ErrorType

DEFAULT_ID = "NULL_ID"


class DeleteStrategy(Enum):
    """
    Specifics strategiy for deletion for Refs
    """

    MUST_BE_EMPTY = auto()
    DELETE_REVERSES_TOO = auto()
    CLEAN_REVERSES = auto()

    def __repr__(self):
        return self.name


class Ref(String):  # pylint: disable=too-many-instance-attributes
    """
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
        on.append(("deletion", self.on_delete))

        String.__init__(
            self,
            default=default,
            required=not_none,
            onchangeDEBUG=self.on_change,
            on=on,
            **kwargs,
        )

    def collection(self):
        """
        Return the collection
        """
        return self._collection

    def reverse(self):
        """
        Return the reverse field fron the other collection
        """
        return self._reverse

    def set_coll_ref(self, root, me):
        """
        Set the reference to the GenericDB object to the collection referenced.
        """
        # Already set
        if me._coll_ref is not None:
            return

        if root is None:
            raise Error(ErrorType.NOAPP, "No root found. WTF")
        if root.app is None:
            raise Error(
                ErrorType.NOAPP, "No app found. A GenericDB not related to an App"
            )
        if me._collection not in root.app.collections:
            raise Error(
                ErrorType.COLLECTION_NOT_FOUND,
                f'Collection "{me._collection}" not found',
            )
        me._coll_ref = root.app.collections[me._collection]

    def on_change(self, old_ref_id, new_id, root): # pylint: disable=unused-argument
        """
        The reference has changed, we have some jobs to do
        """
        # Check if the new one exists
        print(f"on_change {self._collection} {self._reverse}")
        self.check_if_ref_destination_exists(new_id, root)

    def check_if_ref_destination_exists(self, new_id: str, root):
        """
        Check if the Id given exist in the collection
        """
        print(f"check_if_ref_destination_exists {self._collection} {self.get_root()}")
        # set the _coll_ref (in case of)
        self.set_coll_ref(root, self)
        # try to load the coresponding item
        other = self._coll_ref.new()

        # fill the field
        reverse_field = other.select(self._reverse)
        if reverse_field is None:
            raise Error(
                ErrorType.FIELD_NOT_FOUND,
                f'Collection "{self._collection}"."{self._reverse}" not found',
            )

        other.load(new_id)

    def on_created(self, event_name, root, me): # pylint: disable=unused-argument
        """
        The object as been created
        check for the reverse field and modify it
        """
        print(f"on_created {me._collection} {me._reverse}")

        if not me._reverse:
            return

        # set the _coll_ref (in case of)
        me.set_coll_ref(root, me)
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
            reverse_field.set(root._id)
            other.save()
            return

        # List of references
        if isinstance(reverse_field, RefsList):
            if root._id.get_value() not in reverse_field.get_value():
                reverse_field.append(root._id)
                other.save()
            return

        # WTF
        raise Error(
            ErrorType.NOT_A_REF,
             # pylint: disable=line-too-long
            f'Collection "{self._collection}"."{me._reverse}" "{type(reverse_field)}" is not a Ref or a RefsList',
        )

    def on_delete(self, event_name, root, me): # pylint: disable=unused-argument
        """
        The object as been created
        check for the reverse field and modify it
        """

        if not me._reverse:
            return

        if me == DEFAULT_ID:
            return

        # set the _coll_ref (in case of)
        me.set_coll_ref(root, me)
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
                other.save()
            return

        # List of references
        if isinstance(reverse_field, RefsList):
            if root._id.get_value() in reverse_field.get_value():
                reverse_field.remove(root._id.get_value())
                other.save()
            return

        raise Error(
            ErrorType.NOT_A_REF,
            f'Collection "{self._collection}"."{me._reverse}" is not a Ref or a RefsList',
        )


class RefsList(List):
    """
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

        # Strategy for deletion
        on_delete_strategy = kwargs.pop(
            "ods", kwargs.pop("on_delete", DeleteStrategy.MUST_BE_EMPTY)
        )
        if on_delete_strategy == DeleteStrategy.MUST_BE_EMPTY:
            on_delete_strategy = self.on_delete_must_by_empty
        if on_delete_strategy == DeleteStrategy.DELETE_REVERSES_TOO:
            on_delete_strategy = self.on_delete_with_reverse
        if on_delete_strategy == DeleteStrategy.CLEAN_REVERSES:
            on_delete_strategy = self.on_delete_clean_reverse

        # for events
        on = kwargs.pop("on", [])
        on.append(("deletion", on_delete_strategy))

        List.__init__(
            self, String(default=DEFAULT_ID, required=True), on=on, default=[], **kwargs
        )

    def set_coll_ref(self, root, me):
        """
        Set the reference to the GenericDB object to the collection referenced.
        """
        # Already set
        if me._coll_ref is not None:
            return

        if root is None:
            raise Error(ErrorType.NOAPP, "No root found. WTF")
        if root.app is None:
            raise Error(
                ErrorType.NOAPP, "No app found. A GenericDB not related to an App"
            )
        if me._collection not in root.app.collections:
            raise Error(
                ErrorType.COLLECTION_NOT_FOUND,
                f'Collection "{me._collection}" not found',
            )
        me._coll_ref = root.app.collections[me._collection]

    def on_delete_must_by_empty(self, event_name, root, me): # pylint: disable=unused-argument
        """
        The object will be deleted only if this list is empty
        otherwist error
        """
        if len(self) != 0:
            raise Error(
                ErrorType.REFSLIST_NOT_EMPTY,
                f'Collection "{self._collection}" not empty',
            )

    def on_delete_with_reverse(self, event_name, root, me): # pylint: disable=unused-argument
        """
        The object will be deleted too
        otherwist error
        """
        # set the _coll_ref (in case of)
        me.set_coll_ref(root, me)
        # try to load the coresponding field
        for reference in me:
            other = me._coll_ref.new()
            other.load(reference.get_value())
            other.delete()

    def on_delete_clean_reverse(self, event_name, root, me): # pylint: disable=unused-argument
        """
        The reflecting object is cleaned too
        """
        # set the _coll_ref (in case of)
        me.set_coll_ref(root, me)
        # try to load the coresponding field
        for reference in me:
            other = me._coll_ref.new()
            other.load(reference.get_value())

            # get the field
            reverse_field = other.select(me._reverse)
            if reverse_field is None:
                raise Error(
                    ErrorType.FIELD_NOT_FOUND,
                    f'Collection "{self._collection}"."{me._reverse}" not found',
                )

            if not isinstance(reverse_field, Ref):
                raise Error(
                    ErrorType.NOT_A_REF,
                    f'Collection "{self._collection}"."{me._reverse}" is not a Ref or a RefsList',
                )

            if reverse_field == root._id:
                reverse_field.set(None)
                other.save()
