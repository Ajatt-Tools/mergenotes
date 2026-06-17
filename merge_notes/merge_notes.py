# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import itertools
import re
import unicodedata
from collections.abc import Iterable, Iterator, Sequence
from typing import Any

import anki.errors
from anki import collection
from anki.cards import Card, CardId
from anki.collection import OpChanges
from anki.notes import Note, NoteId
from anki.utils import strip_html_media
from aqt import gui_hooks, mw
from aqt.browser import Browser, Table
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import ACTION_NAME, MergeNotesConfig, get_global_config
from .config_types import OriginalNotesAction

######################################################################
# Utils
######################################################################

NUMBERS = str.maketrans("０１２３４５６７８９", "0123456789")


def strip_html(s: str) -> str:
    """Return text with HTML media stripped."""
    return strip_html_media(s).strip()


def strip_punctuation(s: str, config: MergeNotesConfig) -> str:
    """Remove configured punctuation characters from text."""
    for char in frozenset(config.punctuation_characters):
        if char in s:
            s = s.replace(char, "")
    return s


def full_width_to_half_width(s: str) -> str:
    """Normalize full-width characters to half-width equivalents."""
    return unicodedata.normalize("NFKC", s).translate(NUMBERS)


def remove_furigana(s: str) -> str:
    """Remove bracketed furigana from text."""
    return re.sub(r"\s*(\S+)\[[^\[\]]+]", r"\g<1>", s)


def cfg_strip(s: str, config: MergeNotesConfig) -> str:
    """Removes/replaces various characters defined by the user. Called before string comparison."""
    if config.ignore_html_tags:
        s = strip_html(s)
    if config.ignore_furigana:
        s = remove_furigana(s)
    if config.ignore_punctuation:
        s = strip_punctuation(s, config)
    if config.full_width_as_half_width:
        s = full_width_to_half_width(s)
    return s.strip()


def interpret_special_chars(s: str) -> str:
    """Interpret escaped newline, tab, and carriage-return sequences."""
    return s.replace(r"\n", "\n").replace(r"\t", "\t").replace(r"\r", "\r")


def tags_in_notes(notes: Sequence[Note]) -> Iterable[str]:
    """Iterates over all tags present in notes."""
    return itertools.chain(*(note.tags for note in notes))


def fields_in_notes(notes: Sequence[Note]) -> Iterable[str]:
    """Iterates over all field names present in notes."""
    return itertools.chain(*(note.keys() for note in notes))


def merge_tags(recipient: Note, from_notes: Sequence[Note]) -> None:
    """Merge tags from source notes into the recipient note."""
    for tag in tags_in_notes(from_notes):
        if not (recipient.has_tag(tag) or tag == "leech"):
            recipient.add_tag(tag)


def pairs(lst: Sequence[Any]) -> Iterator[tuple[Any, Any]]:
    """Yield adjacent pairs from a sequence."""
    for i in range(len(lst) - 1):
        yield lst[i], lst[i + 1]


def reorder_by_common_fields(notes: Sequence[Note]) -> list[Note]:
    """Sort notes so notes with more shared fields come later."""
    all_fields = frozenset(fields_in_notes(notes))
    return sorted(notes, key=lambda note: sum(int(field_name in all_fields) for field_name in note.keys()))


class MergeNotes:
    """Merge selected notes according to the configured behavior."""

    action_name = f"{ACTION_NAME} of selected cards".capitalize()

    def __init__(self, col: collection.Collection, cfg: MergeNotesConfig) -> None:
        """Store collection and config state for a merge operation."""
        self._cfg = cfg
        self.col = col
        self.notes_to_update: list[Note] = []
        self.nids_to_remove: list[NoteId] = []
        self.nids_to_suspend: list[NoteId] = []
        self.separator = interpret_special_chars(self._cfg.field_separator)

    def op(self, notes: Sequence[Note]) -> OpChanges:
        """Execute the merge operation: merge, update, and optionally suspend or delete original notes."""
        pos = self.col.add_custom_undo_entry(self.action_name)
        self._do_merge(notes)
        self.col.update_notes(self.notes_to_update)
        self.col.remove_notes(self.nids_to_remove)
        self._suspend_cards_of_notes()
        return self.col.merge_undo_entries(pos)

    def _suspend_cards_of_notes(self) -> None:
        """Suspend all cards belonging to the collected note IDs."""
        self.col.sched.suspend_cards(
            [card.id for nid in self.nids_to_suspend for card in self.col.get_note(nid).cards()]
        )

    def _do_merge(self, notes: Sequence[Note]) -> None:
        """Merge notes according to the configured original_notes_action."""
        if self._cfg.avoid_content_loss:
            # notes are already sorted,
            # but additional sorting is required to avoid content loss if possible.
            notes = reorder_by_common_fields(notes)

        action = self._cfg.original_notes_action

        if action in (OriginalNotesAction.delete, OriginalNotesAction.suspend):
            # If the user wants to delete or suspend, dump all content into the last note.
            self._merge_field_content(notes[-1], notes, self.separator)
            other_ids = [note.id for note in notes][0:-1]
            if action is OriginalNotesAction.delete:
                self.nids_to_remove.extend(other_ids)
            else:
                self.nids_to_suspend.extend(other_ids)
            self.notes_to_update.append(notes[-1])
        else:
            # Merge in pairs so that each note receives content of previous notes.
            for add_from, add_to in pairs(notes):
                self._merge_field_content(
                    recipient=add_to,
                    from_notes=(add_from, add_to),
                    separator=self.separator,
                )
            self.notes_to_update.extend(notes)

    def _merge_field_content(self, recipient: Note, from_notes: Sequence[Note], separator: str) -> None:
        """Merge field content from source notes into the recipient note."""
        if self._cfg.merge_tags:
            merge_tags(recipient, from_notes)
        for field_name in self._concerned_field_names(recipient.keys()):
            if recipient[field_name].strip() and self._cfg.skip_if_not_empty:
                continue
            recipient[field_name] = separator.join(
                {
                    cfg_strip(note[field_name], self._cfg): note[field_name]
                    for note in from_notes
                    if field_name in note and note[field_name].strip()
                }.values()
            )

    def _concerned_field_names(self, recipient_fields: list[str]) -> Iterable[str]:
        """
        If the user has limited fields to a certain set, apply the setting.
        """
        if self._cfg.limit_to_fields:
            return frozenset(recipient_fields).intersection(self._cfg.limit_to_fields)
        else:
            return recipient_fields


def notes_by_cards(cards: Iterable[Card]) -> list[Note]:
    """Return unique notes for cards while preserving card iteration order."""
    return list({(note := card.note()).id: note for card in cards}.values())


def is_existing_card(card_id: CardId, browser: Browser) -> bool:
    """Return whether the browser collection still contains a card."""
    try:
        browser.col.get_card(card_id)
    except anki.errors.NotFoundError:
        return False
    else:
        return True


def select_card(self: Table, card_id: CardId) -> None:
    """Select and scroll to a card row in the browser table."""
    self._reset_selection()
    if (row := self._model.get_card_row(card_id)) is not None:
        self._view.selectRow(row)
        self._scroll_to_row(row, scroll_even_if_visible=False)
    else:
        self.browser.on_all_or_selected_rows_changed()
        self.browser.on_current_row_changed()


class BrowserMenus:
    """Browser menu hooks for the Merge Notes action."""

    _cfg: MergeNotesConfig

    def __init__(self, cfg: MergeNotesConfig) -> None:
        """Store config for browser menu callbacks."""
        self._cfg = cfg

    def setup_context_menu(self, browser: Browser) -> None:
        """Add Merge Notes to the browser Cards menu."""
        menu = browser.form.menu_Cards
        merge_fields_action = menu.addAction(ACTION_NAME)
        if shortcut := self._cfg.merge_notes_shortcut:
            merge_fields_action.setShortcut(QKeySequence(shortcut))
        qconnect(merge_fields_action.triggered, lambda: self.on_merge_selected(browser))

    def on_merge_selected(self, browser: Browser) -> None:
        """Merge currently selected browser cards."""
        cids = browser.selectedCards()

        if len(cids) < 2:
            tooltip("At least two cards must be selected.", parent=browser)
            return

        sorted_cards = sorted(
            (browser.col.get_card(cid) for cid in cids),
            key=self._cfg.ord_key,
            reverse=self._cfg.reverse_order,
        )

        if len(notes := notes_by_cards(sorted_cards)) > 1:
            (
                CollectionOp(
                    parent=browser,
                    op=lambda col: MergeNotes(col, self._cfg).op(notes),
                )
                .success(
                    lambda out: self._after_merge(browser, notes, cids),
                )
                .run_in_background()
            )
        else:
            tooltip("At least two distinct notes must be selected.", parent=browser)

    def _adjust_selection(self, browser: Browser, selected_cids: Sequence[int]) -> None:
        """
        If other notes were deleted, select the remaining card after merging.
        Prevent selection from jumping all the way to the top when the user presses arrow keys.
        """
        if self._cfg.original_notes_action is OriginalNotesAction.delete:
            select_card(
                browser.table,
                card_id=next(cid for cid in selected_cids if is_existing_card(cid, browser)),
            )

    def _after_merge(self, browser: Browser, notes: Sequence[Note], cids: Sequence[int]) -> None:
        """Update selection and show a merge completion tooltip."""
        self._adjust_selection(browser, cids)
        tooltip(f"{len(notes)} notes merged.", parent=browser)


######################################################################
# Entry point
######################################################################


def init() -> None:
    """Register browser menu hooks for Merge Notes."""
    assert mw, "Anki should be open."
    cfg = get_global_config()
    menus = BrowserMenus(cfg)
    gui_hooks.browser_menus_did_init.append(menus.setup_context_menu)
