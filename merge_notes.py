# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re
from typing import Sequence, List, Iterator, Any, Tuple

from anki import collection
from anki.cards import Card
from anki.collection import OpChanges
from anki.notes import Note, NoteId
from anki.utils import entsToTxt
from aqt import gui_hooks
from aqt import mw
from aqt.browser import Browser
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import config, OrderingChoices


######################################################################
# Utils
######################################################################


def strip_html(s: str) -> str:
    s = re.sub(r"<img[^<>]+src=[\"']?([^\"'<>]+)[\"']?[^<>]*>", r"\g<1>", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^<>]+>", "", s, flags=re.MULTILINE)
    s = entsToTxt(s)
    s = s.strip()
    return s


def strip_punctuation(s: str) -> str:
    return re.sub(config['punctuation_regexp'], '', s, flags=re.MULTILINE)


def fields_equal(content1: str, content2: str) -> bool:
    if config['strip_punctuation_before_comparison']:
        content1 = strip_punctuation(content1)
        content2 = strip_punctuation(content2)

    if config['html_agnostic_comparison']:
        return strip_html(content1) == strip_html(content2)
    else:
        return content1 == content2


def interpret_special_chars(s: str) -> str:
    return s.replace(r'\n', '\n').replace(r'\t', '\t').replace(r'\r', '\r')


def merge_fields(add_to: Note, add_from: Note, separator: str) -> None:
    for field_name in add_from.keys():
        can_merge = (
                add_from[field_name]
                and field_name in add_to
                and not (config['only_empty'] is True and add_to[field_name])
                and not fields_equal(add_to[field_name], add_from[field_name])
        )

        if can_merge:
            add_to[field_name] = add_to[field_name].strip()
            add_from[field_name] = add_from[field_name].strip()

            if add_to[field_name]:
                add_to[field_name] += separator + add_from[field_name]
            else:
                add_to[field_name] += add_from[field_name]


def merge_tags(add_to: Note, add_from: Note) -> None:
    for tag in add_from.tags:
        if tag == 'leech':
            continue
        if not add_to.has_tag(tag):
            add_to.add_tag(tag)


def pairs(lst: Sequence[Any]) -> Iterator[Tuple[Any, Any]]:
    for i in range(len(lst) - 1):
        yield lst[i], lst[i + 1]


class MergeNotes:
    action_name = "Merge fields of selected cards"

    def __init__(self, col: collection.Collection):
        self.col = col
        self.notes_to_update: List[Note] = []
        self.nids_to_remove: List[NoteId] = []
        self.separator = interpret_special_chars(config['field_separator'])

    def op(self, notes: Sequence[Note]) -> OpChanges:
        pos = self.col.add_custom_undo_entry(self.action_name)
        self._merge_chunk(notes)
        self.col.update_notes(self.notes_to_update)
        self.col.remove_notes(self.nids_to_remove)
        return self.col.merge_undo_entries(pos)

    def _merge_chunk(self, notes: Sequence[Note]):
        for add_from, add_to in pairs(notes):
            merge_fields(add_to, add_from, self.separator)
            if config['merge_tags'] is True:
                merge_tags(add_to, add_from)

        if config['delete_original_notes'] is True:
            self.nids_to_remove.extend([note.id for note in notes][0:-1])
            self.notes_to_update.append(notes[-1])
        else:
            self.notes_to_update.extend(notes)


def notes_by_cards(cards: Sequence[Card]) -> List[Note]:
    return list({(note := card.note()).id: note for card in cards}.values())


def on_merge_selected(browser: Browser) -> None:
    cids = browser.selectedCards()

    if len(cids) < 2:
        tooltip("At least two cards must be selected.")
        return

    sorted_cards = sorted(
        (mw.col.getCard(cid) for cid in cids),
        key=OrderingChoices.get_key(config['ordering']),
        reverse=config['reverse_order']
    )

    if len(notes := notes_by_cards(sorted_cards)) > 1:
        CollectionOp(
            browser, lambda col: MergeNotes(col).op(notes)
        ).success(
            lambda out: tooltip(f"{len(notes)} notes merged.", parent=browser)
        ).run_in_background()
    else:
        tooltip("At least two distinct notes must be selected.")


######################################################################
# Entry point
######################################################################


def setup_context_menu(browser: Browser) -> None:
    menu = browser.form.menu_Cards
    merge_fields_action = menu.addAction("Merge fields")
    merge_fields_action.setShortcut(QKeySequence(config['shortcut']))
    qconnect(merge_fields_action.triggered, lambda: on_merge_selected(browser))


def init():
    gui_hooks.browser_menus_did_init.append(setup_context_menu)
