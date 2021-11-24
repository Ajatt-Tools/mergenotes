# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from gettext import ngettext

from anki.collection import Collection
from anki.notes import Note
from aqt import gui_hooks
from aqt import mw
from aqt.browser import Browser
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import config

LIMIT = 30


def duplicate_notes_op(col: Collection, notes):
    pos = col.add_custom_undo_entry(ngettext("Duplicate %d notes", "Duplicate note", len(notes)) % len(notes))

    for ref_note in notes:
        new_note = Note(col, ref_note.note_type())
        for key in ref_note.keys():
            new_note[key] = ref_note[key]
        new_note.tags = [tag for tag in ref_note.tags if tag != 'leech' and tag != 'marked']
        col.add_note(new_note, deck_id=ref_note.cards()[0].did)

    return col.merge_undo_entries(pos)


def duplicate_notes(browser: Browser):
    notes = [mw.col.get_note(note_id) for note_id in browser.selected_notes()]

    if 1 <= len(notes) <= LIMIT:
        CollectionOp(
            browser, lambda col: duplicate_notes_op(col, notes)
        ).success(
            lambda out: tooltip(
                ngettext("%d notes duplicated.", "Note duplicated.", len(notes)) % len(notes),
                parent=browser
            )
        ).run_in_background()
    else:
        tooltip(f"Please select at most {LIMIT} notes.")


def setup_context_menu(browser: Browser) -> None:
    menu = browser.form.menu_Cards
    action = menu.addAction("Duplicate notes")
    action.setShortcut(QKeySequence(config['dup_note_shortcut']))
    qconnect(action.triggered, lambda: duplicate_notes(browser))


def init():
    gui_hooks.browser_menus_did_init.append(setup_context_menu)
