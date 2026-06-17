# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import enum


@enum.unique
class OriginalNotesAction(enum.Enum):
    """What to do with other selected notes after merging."""

    do_nothing = enum.auto()
    suspend = enum.auto()
    delete = enum.auto()

    @classmethod
    def _missing_(cls, _value: object) -> "OriginalNotesAction":
        """Return the default action for unrecognised config values."""
        return cls.do_nothing
