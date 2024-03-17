# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence

from anki.collection import Collection, OpChanges, AddNoteRequest
from anki.notes import Note
from aqt import gui_hooks
from aqt.browser import Browser
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import config


def n_gettext_duplicate(n_notes: int, is_done: bool) -> str:
    return f"Duplicate{'d' if is_done else ''} {n_notes} note{'s' if n_notes > 1 else ''}"


def duplicate_notes_op(col: Collection, notes: Sequence[Note]) -> OpChanges:
    pos = col.add_custom_undo_entry(n_gettext_duplicate(len(notes), is_done=False))
    requests: list[AddNoteRequest] = []
    for ref_note in notes:
        new_note = Note(col, ref_note.note_type())
        first_card = ref_note.cards()[0]
        for key in ref_note.keys():
            new_note[key] = ref_note[key]
        new_note.tags = [tag for tag in ref_note.tags if tag != "leech" and tag != "marked"]
        requests.append(AddNoteRequest(note=new_note, deck_id=(first_card.odid or first_card.did)))
    col.add_notes(requests)
    return col.merge_undo_entries(pos)


def duplicate_notes(browser: Browser) -> None:
    notes = [browser.col.get_note(note_id) for note_id in browser.selected_notes()]

    if len(notes) > 0:
        (
            CollectionOp(
                parent=browser,
                op=lambda col: duplicate_notes_op(col, notes),
            )
            .success(
                lambda out: tooltip(msg=n_gettext_duplicate(len(notes), is_done=True), parent=browser),
            )
            .run_in_background()
        )
    else:
        tooltip(f"Please select some notes.", parent=browser)


def setup_context_menu(browser: Browser) -> None:
    if config["show_duplicate_notes_button"]:
        menu = browser.form.menu_Cards
        action = menu.addAction("Duplicate notes")
        if shortcut := config["duplicate_notes_shortcut"]:
            action.setShortcut(QKeySequence(shortcut))
        qconnect(action.triggered, lambda: duplicate_notes(browser))


def init():
    gui_hooks.browser_menus_did_init.append(setup_context_menu)
