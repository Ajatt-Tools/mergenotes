# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Sequence, Optional

import anki.errors
from anki.collection import OpChanges
from anki.hooks import wrap
from anki.notes import NoteId, Note
from aqt import mw
from aqt.browser.find_duplicates import FindDuplicatesDialog
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import OrderingChoices, config
from .merge_notes import MergeNotes


def carefully_get_notes(nids: Sequence[NoteId], has_field: Optional[str] = None) -> list[Note]:
    """
    Returns notes constructed from nids. Skip nonexistent notes.
    If "has_field" is not None, return notes that contain this field.
    """
    ret = []
    for nid in nids:
        try:
            note: Note = mw.col.get_note(nid)
            if not has_field or has_field in note.keys():
                ret.append(note)
        except anki.errors.NotFoundError:
            pass
    return ret


def sort_by_note_cards(note: Note):
    return min(OrderingChoices.get_key(config['ordering'])(card) for card in note.cards())


class MergeDupes(MergeNotes):
    action_name = "Merge Duplicates"

    def op(self, dupes: list[tuple[str, list[NoteId]]]) -> OpChanges:
        pos = self.col.add_custom_undo_entry(self.action_name)

        for dupe_string, dupe_nids in dupes:
            if len(chunk := carefully_get_notes(dupe_nids)) > 1:
                chunk.sort(key=sort_by_note_cards, reverse=config['reverse_order'])
                self._merge_chunk(chunk)

        mw.col.update_notes(self.notes_to_update)
        mw.col.remove_notes(self.nids_to_remove)
        return self.col.merge_undo_entries(pos)


def merge_dupes(parent: QWidget, dupes: list[tuple[str, list[NoteId]]]) -> None:
    if len(dupes) > 0:
        CollectionOp(
            parent, lambda col: MergeDupes(col).op(dupes)
        ).success(
            lambda out: tooltip(f"Merged {len(dupes)} groups of notes.")
        ).run_in_background()
    else:
        tooltip("Nothing to do.")


def append_merge_duplicates_button(self: FindDuplicatesDialog, dupes: list[tuple[str, list[NoteId]]]):
    self._dupes = dupes
    if not getattr(self, '_merge_dupes_button', None):
        self._merge_dupes_button = b = self.form.buttonBox.addButton(
            MergeDupes.action_name, QDialogButtonBox.ActionRole
        )
        qconnect(b.clicked, lambda: merge_dupes(parent=self, dupes=self._dupes))


def init():
    FindDuplicatesDialog.show_duplicates_report = wrap(
        FindDuplicatesDialog.show_duplicates_report,
        append_merge_duplicates_button,
        pos="after",
    )
