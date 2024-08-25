# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import sys
from typing import Any, Callable

from anki.cards import Card

from .ajt_common.addon_config import AddonConfigManager

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


class OrderingChoices:
    _choices = {
        "Due": due_key,
        "Interval length": lambda card: card.ivl,
        "Card ID": lambda card: card.id,
        "Deck ID": lambda card: card.did,
        "Sort Field": sort_field_key,
        "Sort Field (numeric)": generic_numeric_key(sort_field_key),
        "Custom field": custom_field_key,
        "Custom field (numeric)": generic_numeric_key(custom_field_key),
    }

    def __getitem__(self, key) -> Callable[[Card], Any]:
        return self._choices[key]

    @classmethod
    def names(cls):
        return cls._choices.keys()


class Config(AddonConfigManager):
    _ordering_choices = OrderingChoices()

    def __init__(self, default: bool = False) -> None:
        super().__init__(default)
        if self["ordering"] not in self._ordering_choices.names():
            print(f"Wrong ordering: {self['ordering']}")
            self["ordering"] = next(name for name in OrderingChoices.names())

    @property
    def ord_key(self):
        return self._ordering_choices[self["ordering"]]

    @classmethod
    def default(cls):
        return cls(default=True)


config = Config()
