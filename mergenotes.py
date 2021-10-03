from typing import Collection, Sequence, List

from anki import collection
from anki.collection import OpChanges
from anki.notes import Note, NoteId
from aqt import gui_hooks
from aqt import mw
from aqt.browser import Browser
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .config import config, OrderingChoices
from .settings_dialog import MergeFieldsSettingsWindow

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


def merge_fields(note1: Note, note2: Note) -> None:
    for field_name, field_value in note2.items():
        # don't waste cycles on empty fields
        # field_name should exist in note1
        if not (field_value and field_name in note1):
            continue

        if config['only_empty'] is True and note1[field_name]:
            continue

        # don't merge equal fields
        if note1[field_name] == note2[field_name]:
            continue

        note1[field_name] = note1[field_name].strip()
        note2[field_name] = note2[field_name].strip()

        if note1[field_name]:
            note1[field_name] += config['field_separator'] + note2[field_name]
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
def merge_cards_fields(col: collection.Collection, cids: Collection) -> OpChanges:
    pos = col.add_custom_undo_entry(ACTION_NAME)
    nids_to_remove = []

    sorted_cards = sorted(
        (mw.col.getCard(cid) for cid in cids),
        key=OrderingChoices.get_key(config['ordering']),
        reverse=config['reverse_order']
    )
    notes = [card.note() for card in sorted_cards]
    merge_notes_fields(notes, nids_to_remove)
    mw.col.update_notes(notes)
    mw.col.remove_notes(nids_to_remove)

    return col.merge_undo_entries(pos)


def on_merge_selected(browser: Browser) -> None:
    cids = browser.selectedCards()

    if len(cids) < 2:
        tooltip("At least two cards must be selected.")
        return

    CollectionOp(
        browser, lambda col: merge_cards_fields(col, cids)
    ).success(
        lambda out: tooltip(f"{len(cids)} cards merged.", parent=browser)
    ).run_in_background()


def on_open_settings() -> None:
    dialog = MergeFieldsSettingsWindow()
    dialog.exec_()


######################################################################
# Entry point
######################################################################


def setup_context_menu(browser: Browser) -> None:
    menu = browser.form.menu_Cards
    merge_fields_action = menu.addAction("Merge fields")
    merge_fields_action.setShortcut(QKeySequence(config['shortcut']))
    qconnect(merge_fields_action.triggered, browser.onMergeSelected)


def setup_edit_menu(browser: Browser) -> None:
    edit_menu = browser.form.menuEdit
    edit_menu.addSeparator()
    merge_fields_settings_action = edit_menu.addAction('Merge Fields Settings...')
    qconnect(merge_fields_settings_action.triggered, on_open_settings)


def on_browser_setup_menus(browser: Browser) -> None:
    setup_context_menu(browser)
    setup_edit_menu(browser)


def init():
    Browser.onMergeSelected = on_merge_selected
    gui_hooks.browser_menus_did_init.append(on_browser_setup_menus)
