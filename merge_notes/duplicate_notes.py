# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence

from anki.collection import AddNoteRequest, Collection, OpChanges
from anki.decks import DeckId
from anki.notes import Note
from aqt import gui_hooks
from aqt.browser import Browser
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import MergeNotesConfig, get_global_config
from .merge_notes import notes_by_cards


def n_gettext_duplicate(n_notes: int, is_done: bool) -> str:
    """Return the status text for duplicating notes."""
    return f"Duplicate{'d' if is_done else ''} {n_notes} note{'s' if n_notes > 1 else ''}"


def find_deck_id(note: Note) -> DeckId:
    """Return the deck ID that should receive a duplicate of the note."""
    first_card = note.cards()[0]
    return first_card.odid or first_card.did


def duplicate_notes_op(col: Collection, notes: Sequence[Note]) -> OpChanges:
    """Duplicate notes and return the resulting collection changes."""
    pos = col.add_custom_undo_entry(n_gettext_duplicate(len(notes), is_done=False))
    requests: list[AddNoteRequest] = []
    for ref_note in notes:
        new_note = Note(col, ref_note.note_type())
        for key in ref_note.keys():
            new_note[key] = ref_note[key]
        new_note.tags = [tag for tag in ref_note.tags if tag != "leech" and tag != "marked"]
        requests.append(AddNoteRequest(note=new_note, deck_id=find_deck_id(ref_note)))
    col.add_notes(requests)
    return col.merge_undo_entries(pos)


def get_notes_keeping_order(browser: Browser) -> list[Note]:
    """
    Retrieve notes in the order they're shown in Browser.
    """
    if browser.table.is_notes_mode():
        return [browser.col.get_note(note_id) for note_id in browser.selected_notes()]
    else:
        return notes_by_cards(browser.col.get_card(card_id) for card_id in browser.selected_cards())


def duplicate_notes(browser: Browser) -> None:
    """Duplicate notes selected in the browser."""
    notes: list[Note] = get_notes_keeping_order(browser)

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


class ContextMenus:
    """Context menu hooks for duplicating notes."""

    def __init__(self, cfg: MergeNotesConfig) -> None:
        """Store the config used by browser menu callbacks."""
        self._cfg = cfg

    def setup_context_menu(self, browser: Browser) -> None:
        """Add the Duplicate Notes action to the browser context menu."""
        if self._cfg.show_duplicate_notes_button:
            menu = browser.form.menu_Cards
            action = menu.addAction("Duplicate notes")
            if shortcut := self._cfg.duplicate_notes_shortcut:
                action.setShortcut(QKeySequence(shortcut))
            qconnect(action.triggered, lambda: duplicate_notes(browser))


def init() -> None:
    """Register browser hooks for duplicate-note actions."""
    cfg = get_global_config()
    menus = ContextMenus(cfg)
    gui_hooks.browser_menus_did_init.append(menus.setup_context_menu)
