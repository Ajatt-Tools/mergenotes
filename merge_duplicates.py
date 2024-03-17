# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Optional
from collections.abc import Sequence

import anki.errors
from anki.collection import OpChanges, Collection
from anki.hooks import wrap
from anki.notes import NoteId, Note
from aqt.browser.find_duplicates import FindDuplicatesDialog
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import config
from .merge_notes import MergeNotes


def carefully_get_notes(col: Collection, nids: Sequence[NoteId], has_field: Optional[str] = None) -> list[Note]:
    """
    Returns notes constructed from nids. Skip nonexistent notes.
    If "has_field" is not None, return notes that contain this field.
    """
    ret: list[Note] = []
    for nid in set(nids):
        try:
            note: Note = col.get_note(nid)
            if not has_field or has_field in note.keys():
                ret.append(note)
        except anki.errors.NotFoundError:
            pass
    return ret


def sort_by_note_cards(note: Note):
    return min(config.ord_key(card) for card in note.cards())


class MergeDupes(MergeNotes):
    action_name = "Merge Duplicates"

    def op(self, dupes: list[tuple[str, list[NoteId]]]) -> OpChanges:
        pos = self.col.add_custom_undo_entry(self.action_name)

        for _, dupe_nids in dupes:
            if len(chunk := carefully_get_notes(self.col, dupe_nids)) > 1:
                chunk.sort(key=sort_by_note_cards, reverse=config["reverse_order"])
                self._merge_notes(chunk)

        self.col.update_notes(self.notes_to_update)
        self.col.remove_notes(self.nids_to_remove)
        return self.col.merge_undo_entries(pos)


def merge_dupes(parent: QWidget, dupes: list[tuple[str, list[NoteId]]]) -> None:
    if len(dupes) > 0:
        (
            CollectionOp(
                parent,
                lambda col: MergeDupes(col).op(dupes),
            )
            .success(
                lambda out: tooltip(f"Merged {len(dupes)} groups of notes.", parent=parent),
            )
            .run_in_background()
        )
    else:
        tooltip("Nothing to do.", parent=parent)


def append_merge_duplicates_button(self: FindDuplicatesDialog, dupes: list[tuple[str, list[NoteId]]]):
    self._dupes = dupes
    if not getattr(self, "_merge_dupes_button", None):
        self._merge_dupes_button = b = self.form.buttonBox.addButton(
            MergeDupes.action_name, QDialogButtonBox.ButtonRole.ActionRole
        )
        qconnect(b.clicked, lambda: merge_dupes(parent=self.browser, dupes=self._dupes))


def init():
    FindDuplicatesDialog.show_duplicates_report = wrap(
        FindDuplicatesDialog.show_duplicates_report,
        append_merge_duplicates_button,
        pos="after",
    )
