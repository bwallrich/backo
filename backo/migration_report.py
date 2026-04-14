"""
Module providing the migration
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

# Importing module
import sys

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import (
    validation_parameters,
    Dict,
    String,
    Int,
    List,
    FreeDict,
)


class MigrationReport(Dict):  # pylint: disable=too-many-instance-attributes
    """The migration report"""

    @validation_parameters
    def __init__(self, **kwargs):
        """
        Constructor
        """

        super().__init__(
            {
                "no_changes": Dict({"_ids": List(String()), "total": Int(default=0)}),
                "changes": Dict(
                    {
                        "_ids": List(String()),
                        "diff": List(FreeDict()),
                        "total": Int(default=0),
                    }
                ),
            },
            **kwargs,
        )

    def add_change(self, _id: str, diff: dict) -> None:
        """Add a changement into the report

        :param _id: _description_the _id concerning with the changement
        :type _id: str
        :param change: the changement as a deepdiff object
        :type change: dict
        """
        self.changes._ids.append(_id)
        self.changes.diff.append(diff)
        self.changes.total = len(self.changes._ids)

    def add_no_change(self, _id: str) -> None:
        """Add a _id without changement into the report

        :param _id: _description_the _id concerning with the changement
        :type _id: str
        """
        self.no_changes._ids.append(_id)
        self.no_changes.total = len(self.no_changes._ids)
