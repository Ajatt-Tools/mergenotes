from typing import List, Tuple, Sequence

from anki.collection import Collection, OpChanges
from anki.hooks import wrap
from anki.notes import NoteId, Note
from aqt import mw
from aqt.browser.find_duplicates import FindDuplicatesDialog
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip
import anki.errors
from .mergenotes import merge_notes_fields

ACTION_NAME = "Merge duplicates"


def carefully_get_notes(nids: Sequence) -> List[Note]:
    ret = []
    for nid in nids:
        try:
            ret.append(mw.col.getNote(nid))
        except anki.errors.NotFoundError:
            pass
    return ret


def merge_op(col: Collection, dupes: List[Tuple[str, List[NoteId]]]) -> OpChanges:
    pos = col.add_custom_undo_entry(ACTION_NAME)
    nids_to_remove = []
    notes = []

    for dupe_string, dupe_nids in dupes:
        notes.extend(chunk := carefully_get_notes(dupe_nids))
        merge_notes_fields(chunk, nids_to_remove)

    mw.col.update_notes(notes)
    mw.col.remove_notes(nids_to_remove)
    return col.merge_undo_entries(pos)


def merge_dupes(parent: QWidget, dupes: List[Tuple[str, List[NoteId]]]) -> None:
    if len(dupes) > 0:
        CollectionOp(
            parent, lambda col: merge_op(col, dupes)
        ).success(
            lambda out: tooltip(f"Merged {len(dupes)} groups of notes.")
        ).run_in_background()
    else:
        tooltip("Nothing to do.")


def append_merge_duplicates_button(self: FindDuplicatesDialog, dupes: List[Tuple[str, List[NoteId]]]):
    self._dupes = dupes
    if not getattr(self, '_merge_dupes_button', None):
        self._merge_dupes_button = b = self.form.buttonBox.addButton(
            ACTION_NAME, QDialogButtonBox.ActionRole
        )
        qconnect(b.clicked, lambda: merge_dupes(parent=self, dupes=self._dupes))


def init():
    FindDuplicatesDialog.show_duplicates_report = wrap(
        FindDuplicatesDialog.show_duplicates_report,
        append_merge_duplicates_button,
        pos="after",
    )
