# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import sys
from typing import Iterable

from anki.cards import Card
from aqt import mw


def due_key(card: Card) -> tuple:
    # sort cards by their type, then by due number,
    # so that new cards are always in the beginning of the list,
    # mimicking the way cards are presented in the Anki Browser
    return card.type, card.due


def sort_field_key(card: Card) -> str:
    return (note := card.note()).values()[note.model()['sortf']]


def sort_field_numeric_key(card: Card) -> tuple[int, str]:
    # Try to imitate sorting Anki does.
    sort_field = sort_field_key(card)
    try:
        return int(sort_field), sort_field
    except ValueError:
        return sys.maxsize, sort_field


class OrderingChoices:
    __choices = {
        "Due": due_key,
        "Sort Field": sort_field_key,
        "Sort Field (numeric)": sort_field_numeric_key,
        "Interval length": lambda card: card.ivl,
        "Card ID": lambda card: card.id,
    }

    @classmethod
    def get_key(cls, key):
        return cls.__choices.get(key)

    @classmethod
    def as_list(cls):
        return [*cls.__choices.keys()]


def get_config() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__)

    if not cfg['ordering'] in OrderingChoices.as_list():
        print(f"Wrong ordering: {cfg['ordering']}")
        cfg['ordering'] = OrderingChoices.as_list()[0]

    return cfg


def get_default_config():
    manager = mw.addonManager
    addon = manager.addonFromModule(__name__)
    return manager.addonConfigDefaults(addon)


class Config:
    _config = get_config()
    _default_config = get_default_config()

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
