import re
from typing import Sequence, List

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

ACTION_NAME = "Merge fields of selected cards"


######################################################################
# Utils
######################################################################


def merge_tags(note1: Note, note2: Note) -> None:
    for tag in note2.tags:
        if tag == 'leech':
            continue
        if not note1.has_tag(tag):
            note1.add_tag(tag)


def strip_html(s: str) -> str:
    s = re.sub(r"<img[^<>]+src=[\"']?([^\"'<>]+)[\"']?[^<>]*>", r"\g<1>", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^<>]+>", "", s, flags=re.MULTILINE)
    s = entsToTxt(s)
    s = s.strip()
    return s


def fields_equal(content1: str, content2: str) -> bool:
    if config['html_agnostic_comparison']:
        return strip_html(content1) == strip_html(content2)
    else:
        return content1 == content2


def interpret_special_chars(s: str) -> str:
    return s.replace(r'\n', '\n').replace(r'\t', '\t').replace(r'\r', '\r')


def merge_fields(note1: Note, note2: Note) -> None:
    for field_name in note2.keys():
        can_merge = (
                note2[field_name]
                and field_name in note1
                and not (config['only_empty'] is True and note1[field_name])
                and not fields_equal(note1[field_name], note2[field_name])
        )

        if can_merge:
            note1[field_name] = note1[field_name].strip()
            note2[field_name] = note2[field_name].strip()

            if note1[field_name]:
                note1[field_name] += interpret_special_chars(config['field_separator']) + note2[field_name]
            else:
                note1[field_name] += note2[field_name]


# Adds content of note2 to note1
def append(note1: Note, note2: Note) -> None:
    merge_fields(note1, note2)

    if config['merge_tags'] is True:
        merge_tags(note1, note2)


def merge_notes_fields(notes: Sequence[Note], nids_to_remove: List[NoteId]):
    if len(notes) > 1:
        # Iterate till 1st element and keep on decrementing i
        for i in reversed(range(len(notes) - 1)):
            append(notes[i], notes[i + 1])

        if config['delete_original_notes'] is True:
            nids_to_remove.extend([note.id for note in notes][1:])


# Col is a collection of cards, cids are the ids of the cards to merge
def merge_cards_fields(col: collection.Collection, notes: Sequence[Note]) -> OpChanges:
    pos = col.add_custom_undo_entry(ACTION_NAME)
    nids_to_remove = []
    merge_notes_fields(notes, nids_to_remove)
    mw.col.update_notes(notes)
    mw.col.remove_notes(nids_to_remove)
    return col.merge_undo_entries(pos)


def notes_by_cards(cards: Sequence[Card]) -> Sequence[Note]:
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
            browser, lambda col: merge_cards_fields(col, notes)
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
    qconnect(merge_fields_action.triggered, browser.onMergeSelected)


def init():
    Browser.onMergeSelected = on_merge_selected
    gui_hooks.browser_menus_did_init.append(setup_context_menu)
