# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import enum
from typing import NamedTuple


class DueSortKey(NamedTuple):
    """Keep new cards ahead of review cards, then compare their due positions."""

    card_type: int
    due: int


class NumericSortKey(NamedTuple):
    """Compare integer field values first, using the original text to break ties."""

    number: int
    text: str


# Each ordering mode produces one comparable key family. Different modes are never mixed in one sort.
SortKey = int | str | DueSortKey | NumericSortKey


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


@enum.unique
class SortOrder(enum.Enum):
    """Sort direction for card ordering."""

    ascending = enum.auto()
    descending = enum.auto()

    @classmethod
    def _missing_(cls, _value: object) -> "SortOrder":
        """Return the default sort order for unrecognised config values."""
        return cls.ascending


@enum.unique
class OrderingChoice(enum.Enum):
    """Ordering choice for card ordering."""

    due = "Due"
    interval_length = "Interval length"
    card_id = "Card ID"
    deck_id = "Deck ID"
    sort_field = "Sort Field"
    sort_field_numeric = "Sort Field (numeric)"
    custom_field = "Custom field"
    custom_field_numeric = "Custom field (numeric)"

    @classmethod
    def _missing_(cls, _value: object) -> "OrderingChoice":
        """Return the default ordering choice for unrecognised config values."""
        return cls.due
