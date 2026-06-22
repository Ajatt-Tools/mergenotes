# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
import sys
from collections.abc import Callable, Mapping
from typing import Any

from anki.cards import Card
from aqt import mw

from .ajt_common.addon_config import AddonConfigManager, set_config_update_action
from .config_types import OriginalNotesAction

ACTION_NAME = "Merge Notes"


def due_key(card: Card) -> tuple:
    """Return Anki's due-order sorting key for a card."""
    # sort cards by their type, then by due number,
    # so that new cards are always in the beginning of the list,
    # mimicking the way cards are presented in the Anki Browser
    return card.type, card.due


def sort_field_key(card: Card) -> str:
    """Return the value of the note type's sort field for a card."""
    return (note := card.note()).values()[note.model()["sortf"]]


def generic_numeric_key(cmp_str_fn: Callable[[Card], str]) -> Callable[[Card], tuple[int, str]]:
    """Return a key function that compares field values numerically when possible."""

    def key(card: Card) -> tuple[int, str]:
        """Return a numeric-first sort key for a card."""
        # Try to imitate sorting Anki does.
        cmp_str = cmp_str_fn(card)
        try:
            return int(cmp_str), cmp_str
        except ValueError:
            return sys.maxsize, cmp_str

    return key


class MergeNotesConfig(AddonConfigManager):
    """Configuration view for the Merge Notes add-on."""

    _ordering_choices: Mapping[str, Callable[[Card], Any]]

    def __init__(self, default: bool = False) -> None:
        """Initialize the config and validate the selected ordering mode."""
        super().__init__(default)
        self._ordering_choices = {
            "Due": due_key,
            "Interval length": lambda card: card.ivl,
            "Card ID": lambda card: card.id,
            "Deck ID": lambda card: card.did,
            "Sort Field": sort_field_key,
            "Sort Field (numeric)": generic_numeric_key(sort_field_key),
            "Custom field": self._custom_field_key,
            "Custom field (numeric)": generic_numeric_key(self._custom_field_key),
        }

        if self["ordering"] not in self._ordering_choices:
            print(f"Wrong ordering: {self['ordering']}")
            self["ordering"] = next(name for name in self._ordering_choices)

    def _custom_field_key(self, card: Card) -> str:
        """Return the configured custom sort field, falling back to the sort field."""
        if (field := self["custom_sort_field"]) in (note := card.note()):
            return note[field]
        else:
            return sort_field_key(card)  # Last resort

    @property
    def ordering_choices(self) -> Mapping[str, Callable[[Card], Any]]:
        """Return all available card ordering choices."""
        return self._ordering_choices

    @property
    def ord_key(self) -> Callable[[Card], Any]:
        """Return the configured card ordering function."""
        return self._ordering_choices[self["ordering"]]

    @property
    def original_notes_action(self) -> OriginalNotesAction:
        """Return the action to take on original notes after merging."""
        try:
            return OriginalNotesAction[self["original_notes_action"]]
        except KeyError:
            return OriginalNotesAction.do_nothing

    @property
    def merge_notes_shortcut(self) -> str:
        """Return the keyboard shortcut for merging notes."""
        return self["merge_notes_shortcut"]

    @property
    def field_separator(self) -> str:
        """Return the separator inserted between merged field values."""
        return self["field_separator"]

    @property
    def avoid_content_loss(self) -> bool:
        """Return whether notes should be reordered to reduce content loss."""
        return bool(self["avoid_content_loss"])

    @property
    def reverse_order(self) -> bool:
        """Return whether cards should be sorted in reverse order."""
        return bool(self["reverse_order"])

    @property
    def merge_tags(self) -> bool:
        """Return whether tags should be merged into the recipient note."""
        return bool(self["merge_tags"])

    @property
    def skip_if_not_empty(self) -> bool:
        """Return whether non-empty recipient fields should be left unchanged."""
        return bool(self["skip_if_not_empty"])

    @property
    def punctuation_characters(self) -> str:
        """Return characters ignored when comparing fields."""
        return self["punctuation_characters"]

    @property
    def ignore_html_tags(self) -> bool:
        """Return whether HTML tags should be stripped before comparison."""
        return bool(self["ignore_html_tags"])

    @property
    def ignore_furigana(self) -> bool:
        """Return whether furigana should be ignored before comparison."""
        return bool(self["ignore_furigana"])

    @property
    def ignore_punctuation(self) -> bool:
        """Return whether punctuation should be ignored before comparison."""
        return bool(self["ignore_punctuation"])

    @property
    def full_width_as_half_width(self) -> bool:
        """Return whether full-width characters should be normalized."""
        return bool(self["full-width_as_half-width"])

    @property
    def limit_to_fields(self) -> list[str]:
        """Return field names that should be affected by merging."""
        return self["limit_to_fields"]

    @property
    def ordering(self) -> str:
        """Return the selected card ordering name."""
        return self["ordering"]

    @property
    def custom_sort_field(self) -> str:
        """Return the custom sort field name."""
        return self["custom_sort_field"]

    @property
    def show_duplicate_notes_button(self) -> bool:
        """Return whether the Duplicate Notes browser action is shown."""
        return bool(self["show_duplicate_notes_button"])

    @property
    def duplicate_notes_shortcut(self) -> str:
        """Return the keyboard shortcut for duplicating notes."""
        return self["duplicate_notes_shortcut"]

    @property
    def apply_when_searching_duplicates(self) -> bool:
        """Return whether duplicate search should use Merge Notes comparisons."""
        return bool(self["apply_when_searching_duplicates"])

    @classmethod
    def default(cls) -> "MergeNotesConfig":
        """Return a config view backed by default values."""
        return cls(default=True)


@functools.cache
def get_global_config() -> MergeNotesConfig:
    """Return the cached global config view for the running Anki session."""
    assert mw, "anki must be running"
    config = MergeNotesConfig()
    set_config_update_action(config.update_from_addon_manager)
    return config
