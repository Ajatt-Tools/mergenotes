# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Iterable, Callable

from anki.collection import Collection
from anki.collection import SearchNode
from anki.hooks import wrap
from anki.notes import Note

from .config import config
from .merge_duplicates import carefully_get_notes
from .merge_notes import cfg_strip


def notes_from_search(self: Collection, field_name: str, search: str) -> Iterable[Note]:
    return carefully_get_notes(self.find_notes(
        self.build_search_string(search, SearchNode(field_name=field_name))
    ), has_field=field_name)


def deep_search_duplicates(self: Collection, field_name: str, search: str) -> list[tuple[str, list]]:
    vals = {}
    notes = notes_from_search(self, field_name, search)
    for note in notes:
        if val := cfg_strip(note[field_name]):
            vals.setdefault(val, []).append(note.id)
    return [(dupe_str, dupe_list) for dupe_str, dupe_list in vals.items() if len(dupe_list) >= 2]


def find_duplicates(self: Collection, field_name: str, search: str, _old: Callable) -> list[tuple[str, list]]:
    if config.get('apply_when_searching_duplicates'):
        return deep_search_duplicates(self, field_name, search)
    else:
        return _old(self, field_name, search)


def init():
    Collection.find_dupes = wrap(Collection.find_dupes, find_duplicates, pos='around')
