# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import itertools
import re
import unicodedata
from typing import Sequence, Iterator, Any, Iterable

from anki import collection
from anki.cards import Card, CardId
from anki.collection import OpChanges
from anki.notes import Note, NoteId
from anki.utils import strip_html_media
from aqt import gui_hooks
from aqt import mw
from aqt.browser import Browser, Table
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import config


######################################################################
# Utils
######################################################################


def strip_html(s: str) -> str:
    return strip_html_media(s).strip()


def strip_punctuation(s: str) -> str:
    for char in set(config['punctuation_characters']):
        if char in s:
            s = s.replace(char, '')
    return s


def full_width_to_half_width(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def remove_furigana(s: str):
    return re.sub(r'\s*(\S+)\[[^\[\]]+]', r'\g<1>', s)


def cfg_strip(s: str) -> str:
    """Removes/replaces various characters defined by the user. Called before string comparison."""
    if config['ignore_html_tags']:
        s = strip_html(s)
    if config['ignore_furigana']:
        s = remove_furigana(s)
    if config['ignore_punctuation']:
        s = strip_punctuation(s)
    if config['full-width_as_half-width']:
        s = full_width_to_half_width(s)
    return s.strip()


def interpret_special_chars(s: str) -> str:
    return s.replace(r'\n', '\n').replace(r'\t', '\t').replace(r'\r', '\r')


def tags_in_notes(notes: Sequence[Note]) -> Iterable[str]:
    """Iterates over all tags present in notes."""
    return itertools.chain(*(note.tags for note in notes))


def fields_in_notes(notes: Sequence[Note]) -> Iterable[str]:
    """Iterates over all field names present in notes."""
    return itertools.chain(*(note.keys() for note in notes))


def merge_tags(recipient: Note, from_notes: Sequence[Note]) -> None:
    for tag in tags_in_notes(from_notes):
        if not (recipient.has_tag(tag) or tag == 'leech'):
            recipient.add_tag(tag)


def merge_notes(recipient: Note, from_notes: Sequence[Note], separator: str):
    if config['merge_tags'] is True:
        merge_tags(recipient, from_notes)
    for field_name in recipient.keys():
        if recipient[field_name].strip() and config['skip_if_not_empty'] is True:
            continue
        recipient[field_name] = separator.join(
            {
                cfg_strip(note[field_name]): note[field_name]
                for note in from_notes
                if field_name in note and note[field_name].strip()
            }.values()
        )


def pairs(lst: Sequence[Any]) -> Iterator[tuple[Any, Any]]:
    for i in range(len(lst) - 1):
        yield lst[i], lst[i + 1]


def reorder_by_common_fields(notes: Sequence[Note]) -> list[Note]:
    all_fields = set(fields_in_notes(notes))
    return sorted(notes, key=lambda note: sum(int(field_name in all_fields) for field_name in note.keys()))


class MergeNotes:
    action_name = "Merge fields of selected cards"

    def __init__(self, col: collection.Collection):
        self.col = col
        self.notes_to_update: list[Note] = []
        self.nids_to_remove: list[NoteId] = []
        self.separator = interpret_special_chars(config['field_separator'])

    def op(self, notes: Sequence[Note]) -> OpChanges:
        pos = self.col.add_custom_undo_entry(self.action_name)
        self._merge_chunk(notes)
        self.col.update_notes(self.notes_to_update)
        self.col.remove_notes(self.nids_to_remove)
        return self.col.merge_undo_entries(pos)

    def _merge_chunk(self, notes: Sequence[Note]):
        if config['avoid_content_loss']:
            # notes are already sorted,
            # but additional sorting is required to avoid content loss if possible.
            notes = reorder_by_common_fields(notes)

        if config['delete_original_notes'] is True:
            # If the user wants to delete original notes, simply dump all content into the last note.
            merge_notes(notes[-1], notes, self.separator)
            self.nids_to_remove.extend([note.id for note in notes][0:-1])
            self.notes_to_update.append(notes[-1])
        else:
            # If not, merge in pairs so that each note receives content of previous notes.
            for add_from, add_to in pairs(notes):
                merge_notes(add_to, (add_from, add_to,), self.separator)
            self.notes_to_update.extend(notes)


def notes_by_cards(cards: Sequence[Card]) -> list[Note]:
    return list({(note := card.note()).id: note for card in cards}.values())


def is_existing_card(card_id: CardId) -> bool:
    import anki
    try:
        mw.col.get_card(card_id)
    except anki.errors.NotFoundError:
        return False
    else:
        return True


def select_card(self: Table, card_id: CardId):
    self._reset_selection()
    if (row := self._model.get_card_row(card_id)) is not None:
        self._view.selectRow(row)
        self._scroll_to_row(row, scroll_even_if_visible=False)
    else:
        self.browser.on_all_or_selected_rows_changed()
        self.browser.on_current_row_changed()


def adjust_selection(browser: Browser, selected_cids: Sequence[int]):
    """
    If other notes were deleted, select the remaining card after merging.
    Prevent selection from jumping all the way to the top when the user presses arrow keys.
    """
    if config['delete_original_notes'] is True:
        select_card(
            browser.table,
            card_id=next(cid for cid in selected_cids if is_existing_card(cid))
        )


def after_merge(browser: Browser, notes: Sequence[Note], cids: Sequence[int]):
    adjust_selection(browser, cids)
    tooltip(f"{len(notes)} notes merged.", parent=browser)


def on_merge_selected(browser: Browser) -> None:
    cids = browser.selectedCards()

    if len(cids) < 2:
        tooltip("At least two cards must be selected.")
        return

    sorted_cards = sorted(
        (mw.col.get_card(cid) for cid in cids),
        key=config.ord_key,
        reverse=config['reverse_order']
    )

    if len(notes := notes_by_cards(sorted_cards)) > 1:
        CollectionOp(
            browser, lambda col: MergeNotes(col).op(notes)
        ).success(
            lambda out: after_merge(browser, notes, cids)
        ).run_in_background()
    else:
        tooltip("At least two distinct notes must be selected.")


######################################################################
# Entry point
######################################################################


def setup_context_menu(browser: Browser) -> None:
    menu = browser.form.menu_Cards
    merge_fields_action = menu.addAction("Merge fields")
    if shortcut := config['merge_notes_shortcut']:
        merge_fields_action.setShortcut(QKeySequence(shortcut))
    qconnect(merge_fields_action.triggered, lambda: on_merge_selected(browser))


def init():
    gui_hooks.browser_menus_did_init.append(setup_context_menu)
