# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import sys
from typing import Iterable, Callable, Any

from anki.cards import Card
from aqt import mw


def due_key(card: Card) -> tuple:
    # sort cards by their type, then by due number,
    # so that new cards are always in the beginning of the list,
    # mimicking the way cards are presented in the Anki Browser
    return card.type, card.due


def sort_field_key(card: Card) -> str:
    return (note := card.note()).values()[note.model()['sortf']]


def custom_field_key(card: Card) -> str:
    if (field := config['custom_sort_field']) in (note := card.note()):
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


def get_config() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__)

    if not cfg['ordering'] in OrderingChoices.names():
        print(f"Wrong ordering: {cfg['ordering']}")
        cfg['ordering'] = next(iter(OrderingChoices.names()))

    return cfg


def get_default_config():
    manager = mw.addonManager
    addon = manager.addonFromModule(__name__)
    return manager.addonConfigDefaults(addon)


class Config:
    _config = get_config()
    _default_config = get_default_config()
    _ordering_choices = OrderingChoices()

    def __init__(self, default: bool = False):
        if default:
            self._config = self._default_config

    def __getitem__(self, item):
        if item in self._default_config.keys():
            return self._config[item]
        else:
            raise RuntimeError("Invalid config key.")

    def __setitem__(self, key, value):
        if key in self._default_config.keys():
            self._config[key] = value
        else:
            raise RuntimeError("Invalid config key.")

    @property
    def ord_key(self):
        return self._ordering_choices[self['ordering']]

    @classmethod
    def bool_keys(cls) -> Iterable[str]:
        for key, value in cls._default_config.items():
            if type(value) == bool:
                yield key

    @property
    def is_default(self) -> bool:
        return self._config is self._default_config

    @classmethod
    def default(cls):
        return cls(default=True)

    def write(self):
        if not self.is_default:
            return mw.addonManager.writeConfig(__name__, self._config)
        else:
            raise RuntimeError("Cannot write default config.")


config = Config()
