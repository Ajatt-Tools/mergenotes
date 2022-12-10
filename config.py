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


def write_config():
    return mw.addonManager.writeConfig(__name__, config)


def fetch_config_toggleables() -> Iterable[str]:
    for key, value in config.items():
        if type(value) == bool:
            yield key


config = get_config()
