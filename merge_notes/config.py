# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools
import sys
from typing import Any, Callable, Final

from anki.cards import Card
from aqt import mw

from .ajt_common.addon_config import AddonConfigManager, set_config_update_action
from .config_types import OriginalNotesAction

ACTION_NAME = "Merge Notes"


def due_key(card: Card) -> tuple:
    # sort cards by their type, then by due number,
    # so that new cards are always in the beginning of the list,
    # mimicking the way cards are presented in the Anki Browser
    return card.type, card.due


def sort_field_key(card: Card) -> str:
    return (note := card.note()).values()[note.model()["sortf"]]


def custom_field_key(card: Card) -> str:
    if (field := config["custom_sort_field"]) in (note := card.note()):
        return note[field]
    else:
        return sort_field_key(card)  # Last resort


def generic_numeric_key(cmp_str_fn: Callable[[Card], str]) -> Callable[[Card], tuple[int, str]]:
    def key(card: Card):
        # Try to imitate sorting Anki does.
        cmp_str = cmp_str_fn(card)
        try:
            return int(cmp_str), cmp_str
        except ValueError:
            return sys.maxsize, cmp_str

    return key


ORDERING_CHOICES: Final[dict[str, Callable[[Card], Any]]] = {
    "Due": due_key,
    "Interval length": lambda card: card.ivl,
    "Card ID": lambda card: card.id,
    "Deck ID": lambda card: card.did,
    "Sort Field": sort_field_key,
    "Sort Field (numeric)": generic_numeric_key(sort_field_key),
    "Custom field": custom_field_key,
    "Custom field (numeric)": generic_numeric_key(custom_field_key),
}


class MergeNotesConfig(AddonConfigManager):
    def __init__(self, default: bool = False) -> None:
        super().__init__(default)
        if self["ordering"] not in ORDERING_CHOICES:
            print(f"Wrong ordering: {self['ordering']}")
            self["ordering"] = next(name for name in ORDERING_CHOICES)

    @property
    def ord_key(self) -> Callable[[Card], Any]:
        return ORDERING_CHOICES[self["ordering"]]

    @property
    def original_notes_action(self) -> OriginalNotesAction:
        """Return the action to take on original notes after merging."""
        try:
            return OriginalNotesAction[self["original_notes_action"]]
        except KeyError:
            return OriginalNotesAction.do_nothing

    @property
    def merge_notes_shortcut(self) -> str:
        return self["merge_notes_shortcut"]

    @property
    def field_separator(self) -> str:
        return self["field_separator"]

    @property
    def avoid_content_loss(self) -> bool:
        return bool(self["avoid_content_loss"])

    @classmethod
    def default(cls):
        return cls(default=True)


@functools.cache
def get_global_config() -> MergeNotesConfig:
    assert mw, "anki must be running"
    config = MergeNotesConfig()
    set_config_update_action(config.update_from_addon_manager)
    return config


if mw:
    config = get_global_config()
