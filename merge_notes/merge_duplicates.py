# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence
from typing import Optional

import anki.errors
from anki.collection import Collection, OpChanges
from anki.hooks import wrap
from anki.notes import Note, NoteId
from aqt import mw
from aqt.browser.find_duplicates import FindDuplicatesDialog
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import MergeNotesConfig, get_global_config
from .config_types import SortOrder
from .merge_notes import MergeNotes


def carefully_get_notes(col: Collection, nids: Sequence[NoteId], has_field: Optional[str] = None) -> list[Note]:
    """
    Returns notes constructed from nids. Skip nonexistent notes.
    If "has_field" is not None, return notes that contain this field.
    """
    ret: list[Note] = []
    for nid in frozenset(nids):
        try:
            note: Note = col.get_note(nid)
            if not has_field or has_field in note.keys():
                ret.append(note)
        except anki.errors.NotFoundError:
            pass
    return ret


class MergeDupes(MergeNotes):
    """Merge duplicate-note groups reported by Anki."""

    action_name = "Merge Duplicates"

    def _sort_by_note_cards(self, note: Note) -> object:
        """Return the smallest configured sort key among a note's cards."""
        return min(self._cfg.ord_key(card) for card in note.cards())

    def op(self, dupes: list[tuple[str, list[NoteId]]]) -> OpChanges:
        """Merge all duplicate groups and return collection changes."""
        pos = self.col.add_custom_undo_entry(self.action_name)

        for _, dupe_nids in dupes:
            if len(chunk := carefully_get_notes(self.col, dupe_nids)) > 1:
                chunk.sort(key=self._sort_by_note_cards, reverse=self._cfg.sort_order is SortOrder.descending)
                self._do_merge(chunk)

        self.col.update_notes(self.notes_to_update)
        self.col.remove_notes(self.nids_to_remove)
        return self.col.merge_undo_entries(pos)


class MergeDuplicatesMenus:
    """Menu hooks for merging duplicate-note search results."""

    def __init__(self, cfg: MergeNotesConfig) -> None:
        """Store the config used by duplicate-merge callbacks."""
        self._cfg = cfg

    def append_merge_duplicates_button(
        self, dialog: FindDuplicatesDialog, dupes: list[tuple[str, list[NoteId]]]
    ) -> None:
        """Add the Merge Duplicates button to Anki's duplicate report dialog."""
        dialog._dupes = dupes
        if not getattr(dialog, "_merge_dupes_button", None):
            dialog._merge_dupes_button = b = dialog.form.buttonBox.addButton(
                MergeDupes.action_name, QDialogButtonBox.ButtonRole.ActionRole
            )
            qconnect(b.clicked, lambda: self._merge_dupes(parent=dialog.browser, dupes=dialog._dupes))

    def _merge_dupes(self, parent: QWidget, dupes: list[tuple[str, list[NoteId]]]) -> None:
        """Run the merge operation for duplicate groups."""
        if len(dupes) > 0:
            (
                CollectionOp(
                    parent,
                    lambda col: MergeDupes(col, self._cfg).op(dupes),
                )
                .success(
                    lambda out: tooltip(f"Merged {len(dupes)} groups of notes.", parent=parent),
                )
                .run_in_background()
            )
        else:
            tooltip("Nothing to do.", parent=parent)


def init() -> None:
    """Install hooks for adding Merge Duplicates to the duplicate report dialog."""
    assert mw, "Anki should be open."
    cfg = get_global_config()
    menus = MergeDuplicatesMenus(cfg)
    FindDuplicatesDialog.show_duplicates_report = wrap(
        FindDuplicatesDialog.show_duplicates_report,
        menus.append_merge_duplicates_button,
        pos="after",
    )
