# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import sys
from typing import Tuple

from anki.cards import Card
from aqt import mw


def due_key(card: Card) -> tuple:
    # sort cards by their type, then by due number,
    # so that new cards are always in the beginning of the list,
    # mimicking the way cards are presented in the Anki Browser
    return card.type, card.due


def sort_field_key(card: Card) -> str:
    return (note := card.note()).values()[note.model()['sortf']]


def sort_field_numeric_key(card: Card) -> Tuple[int, str]:
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
    }

    @classmethod
    def get_key(cls, key):
        return cls.__choices.get(key)

    @classmethod
    def as_list(cls):
        return [*cls.__choices.keys()]


def get_config() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__)
    cfg['delete_original_notes']: bool = cfg.get('delete_original_notes', False)
    cfg['merge_tags']: bool = cfg.get('merge_tags', True)
    cfg['only_empty']: bool = cfg.get('only_empty', False)
    cfg['reverse_order']: bool = cfg.get('reverse_order', False)
    cfg['field_separator']: str = cfg.get('field_separator', "")
    cfg['merge_notes_shortcut']: str = cfg.get('merge_notes_shortcut', "Ctrl+Alt+M")
    cfg['ordering']: str = cfg.get('ordering', "Due")

    if not cfg['ordering'] in OrderingChoices.as_list():
        print('Wrong ordering:', cfg['ordering'])
        cfg['ordering'] = OrderingChoices.get_key("Due")

    return cfg


def write_config():
    return mw.addonManager.writeConfig(__name__, config)


config = get_config()
