# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Iterable

import aqt
from anki.collection import Collection
from anki.collection import SearchNode
from anki.hooks import wrap
from anki.notes import Note
from aqt.browser import Browser
from aqt.browser.find_duplicates import FindDuplicatesDialog
from aqt.qt import *

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


def append_apply_checkbox(self: FindDuplicatesDialog, _browser: Browser, _mw: aqt.AnkiQt):
    # row, column, rowSpan, columnSpan
    self.form.gridLayout.addWidget(c := QCheckBox("Use Merge Notes search algorithm"), 3, 1, 1, 2)
    c.setChecked(bool(config.get('apply_when_searching_duplicates')))

    def on_state_changed(checked: int):
        # Ref: https://doc.qt.io/qt-6/qt.html#CheckState-enum
        config['apply_when_searching_duplicates'] = bool(checked)

    qconnect(c.stateChanged, on_state_changed)


def init():
    Collection.find_dupes = wrap(
        Collection.find_dupes,
        find_duplicates,
        pos="around",
    )
    FindDuplicatesDialog.__init__ = wrap(
        FindDuplicatesDialog.__init__,
        append_apply_checkbox,
        pos="after",
    )
