# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Iterable

import aqt
from anki.collection import Collection, SearchNode
from anki.hooks import wrap
from anki.notes import Note, NoteId
from aqt.browser import Browser
from aqt.browser.find_duplicates import FindDuplicatesDialog
from aqt.qt import *

from .config import ACTION_NAME, MergeNotesConfig, get_global_config
from .merge_duplicates import carefully_get_notes
from .merge_notes import cfg_strip


def notes_from_search(col: Collection, field_name: str, search: str) -> Iterable[Note]:
    """Return notes matching the duplicate-search field and query."""
    return carefully_get_notes(
        col,
        col.find_notes(query=col.build_search_string(search, SearchNode(field_name=field_name))),
        has_field=field_name,
    )


class FindDuplicatesMenus:
    """Hooks that enhance Anki's Find Duplicates dialog."""

    def __init__(self, cfg: MergeNotesConfig) -> None:
        """Store the config used by duplicate-search hooks."""
        self._cfg = cfg

    def append_apply_checkbox(self, dialog: FindDuplicatesDialog, _browser: Browser, _mw: aqt.AnkiQt) -> None:
        """Add a checkbox that toggles Merge Notes duplicate comparison."""
        # row, column, rowSpan, columnSpan
        dialog.form.verticalLayout.addWidget(c := QCheckBox(f"Search with {ACTION_NAME}"))
        c.setChecked(self._cfg.apply_when_searching_duplicates)

        def on_state_changed(checked: int) -> None:
            """Persist the checkbox state in the config."""
            # Ref: https://doc.qt.io/qt-6/qt.html#CheckState-enum
            self._cfg["apply_when_searching_duplicates"] = bool(checked)

        qconnect(c.stateChanged, on_state_changed)

    def find_duplicates(self, col: Collection, field_name: str, search: str, _old: Callable) -> list[tuple[str, list]]:
        """Find duplicates using Merge Notes comparison when enabled."""
        if self._cfg.apply_when_searching_duplicates:
            return self._deep_search_duplicates(col, field_name, search)
        else:
            return _old(col, field_name, search)

    def _deep_search_duplicates(self, col: Collection, field_name: str, search: str) -> list[tuple[str, list]]:
        """Find duplicate notes after normalizing field values."""
        vals: dict[str, list[NoteId]] = {}
        for note in notes_from_search(col, field_name, search):
            if val := cfg_strip(note[field_name], self._cfg):
                vals.setdefault(val, []).append(note.id)
        return [(dupe_str, dupe_list) for dupe_str, dupe_list in vals.items() if len(dupe_list) >= 2]


def init() -> None:
    """Install Find Duplicates dialog hooks."""
    assert aqt.mw, "Anki should be open."
    cfg = get_global_config()
    menus = FindDuplicatesMenus(cfg)
    Collection.find_dupes = wrap(
        Collection.find_dupes,
        menus.find_duplicates,
        pos="around",
    )
    FindDuplicatesDialog.__init__ = wrap(
        FindDuplicatesDialog.__init__,
        menus.append_apply_checkbox,
        pos="after",
    )
