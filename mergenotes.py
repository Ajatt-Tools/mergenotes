from gettext import gettext as _
from typing import Collection

from anki.cards import Card
from anki.notes import Note
from aqt import gui_hooks
from aqt import mw
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import tooltip


######################################################################
# Utils
######################################################################

def due_key(card: Card) -> tuple:
    # sort cards by their type, then by due number,
    # so that new cards are always in the beginning of the list,
    # mimicking the way cards are presented in the Anki Browser
    return card.type, card.due


def sort_field_key(card: Card) -> str:
    note: Note = card.note()
    return note.values()[note.model()['sortf']]


class OrderingChoices:
    __choices = {
        "Due": due_key,
        "Sort Field": sort_field_key
    }

    @classmethod
    def get_key(cls, key):
        return cls.__choices.get(key)

    @classmethod
    def as_list(cls):
        return [*cls.__choices.keys()]


def get_config() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__)
    cfg['delete_original_notes']: bool = cfg.get('delete_original_notes', False)
    cfg['merge_tags']: bool = cfg.get('merge_tags', True)
    cfg['only_empty']: bool = cfg.get('only_empty', False)
    cfg['reverse_order']: bool = cfg.get('reverse_order', False)
    cfg['field_separator']: str = cfg.get('field_separator', "")
    cfg['shortcut']: str = cfg.get('shortcut', "Ctrl+Alt+M")
    cfg['ordering']: str = cfg.get('ordering', "Due")

    if not cfg['ordering'] in OrderingChoices.as_list():
        print('Wrong ordering:', cfg['ordering'])
        cfg['ordering'] = OrderingChoices.get_key("Due")

    return cfg


def merge_tags(note1: Note, note2: Note) -> None:
    for tag in note2.tags:
        if tag == 'leech':
            continue
        if not note1.hasTag(tag):
            note1.addTag(tag)


def merge_fields(note1: Note, note2: Note) -> None:
    for (field_name, field_value) in note2.items():
        # don't waste cycles on empty fields
        # field_name should exist in note1
        if not (field_value and field_name in note1):
            continue

        if config['only_empty'] is True and note1[field_name]:
            continue

        # don't merge equal fields
        if note1[field_name] != note2[field_name]:
            note1[field_name] += config['field_separator'] + note2[field_name]


# Adds content of note2 to note1
def append(note1: Note, note2: Note) -> None:
    merge_fields(note1, note2)

    if config['merge_tags'] is True:
        merge_tags(note1, note2)

    note1.flush()


# Col is a collection of cards, cids are the ids of the cards to merge
def merge_cards_fields(cids: Collection) -> None:
    cards = [mw.col.getCard(cid) for cid in cids]
    cards = sorted(cards, key=OrderingChoices.get_key(config['ordering']), reverse=config['reverse_order'])
    
    # Include notes only once
    notes = []
    for card in cards:
        note = card.note()
        if note.id not in [n.id for n in notes]:
            notes.append(note)

    # Iterate till 1st element and keep on decrementing i
    for i in reversed(range(len(notes) - 1)):
        append(notes[i], notes[i + 1])

    if config['delete_original_notes'] is True:
        mw.col.remNotes([note.id for note in notes][1:])


def on_merge_selected(browser: Browser) -> None:
    cids = browser.selectedCards()

    if len(cids) < 2:
        tooltip("At least two cards must be selected.")
        return

    browser.model.beginReset()
    browser.mw.checkpoint(_("Merge fields of selected cards"))

    merge_cards_fields(cids)

    browser.model.endReset()
    browser.mw.reset()

    tooltip(f"{len(cids)} cards merged.", parent=browser)


def on_open_settings() -> None:
    dialog = MergeFieldsSettingsWindow()
    dialog.exec_()


######################################################################
# UI Layout
######################################################################

class DialogUI(QDialog):
    def __init__(self, *args, **kwargs):
        super(DialogUI, self).__init__(parent=mw, *args, **kwargs)
        self.fieldSeparatorLineEdit = QLineEdit()
        self.orderingComboBox = QComboBox()
        self.deleteOriginalNotesCheckBox = QCheckBox("Delete original notes")
        self.mergeTagsCheckBox = QCheckBox("Merge tags")
        self.reverseOrderCheckBox = QCheckBox("Reverse order")
        self.onlyEmptyCheckBox = QCheckBox("Only empty")
        self.okButton = QPushButton("Ok")
        self.cancelButton = QPushButton("Cancel")
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle('Merge Fields Settings')
        self.setLayout(self.setup_outer_layout())
        self.add_tooltips()

    def setup_outer_layout(self):
        vbox = QVBoxLayout()
        vbox.setSpacing(10)
        vbox.addLayout(self.create_top_group())
        vbox.addLayout(self.create_checkbox_group())
        vbox.addStretch(1)
        vbox.addLayout(self.create_bottom_group())
        return vbox

    def create_top_group(self):
        grid = QGridLayout()
        grid.addWidget(QLabel("Field Separator:"), 0, 0)
        grid.addWidget(self.fieldSeparatorLineEdit, 0, 1)
        grid.addWidget(QLabel("Ordering:"), 1, 0)
        grid.addWidget(self.orderingComboBox, 1, 1)
        return grid

    def create_checkbox_group(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.deleteOriginalNotesCheckBox)
        vbox.addWidget(self.mergeTagsCheckBox)
        vbox.addWidget(self.reverseOrderCheckBox)
        vbox.addWidget(self.onlyEmptyCheckBox)
        return vbox

    def create_bottom_group(self):
        hbox = QHBoxLayout()
        hbox.addWidget(self.okButton)
        hbox.addWidget(self.cancelButton)
        hbox.addStretch()
        return hbox

    def add_tooltips(self):
        self.fieldSeparatorLineEdit.setToolTip(
            "This string is inserted between the merged fields.\n"
            "Empty by default.\n"
            "Common options would be to change it to a single space: \" \",\n"
            "or to a linebreak: \"<br>\"."
        )
        self.deleteOriginalNotesCheckBox.setToolTip("Delete redundant notes after merging.")
        self.mergeTagsCheckBox.setToolTip("Merge tags of selected notes in addition to contents of fields.")
        self.reverseOrderCheckBox.setToolTip(
            "Sort cards in reverse.\n"
            "For Due ordering this would mean\n"
            "that a card with the biggest due number\n"
            "will receive the content of other selected cards."
        )
        self.onlyEmptyCheckBox.setToolTip("Copy only from non-empty fields to empty fields.")


######################################################################
# Settings window
######################################################################

class MergeFieldsSettingsWindow(DialogUI):
    def __init__(self):
        super().__init__()
        self.populate_ordering_combobox()
        self.load_config_values()
        self.connect_ui_elements()

    def populate_ordering_combobox(self):
        self.orderingComboBox.addItems(OrderingChoices.as_list())

    def load_config_values(self):
        self.fieldSeparatorLineEdit.setText(config['field_separator'])
        self.orderingComboBox.setCurrentText(config['ordering'])

        self.deleteOriginalNotesCheckBox.setChecked(config['delete_original_notes'])
        self.mergeTagsCheckBox.setChecked(config['merge_tags'])
        self.reverseOrderCheckBox.setChecked(config['reverse_order'])
        self.onlyEmptyCheckBox.setChecked(config['only_empty'])

    def connect_ui_elements(self):
        qconnect(self.cancelButton.clicked, self.reject)
        qconnect(self.okButton.clicked, self.on_confirm)

    def on_confirm(self):
        config['field_separator']: str = self.fieldSeparatorLineEdit.text()
        config['ordering']: str = self.orderingComboBox.currentText()

        config['delete_original_notes']: bool = self.deleteOriginalNotesCheckBox.isChecked()
        config['merge_tags']: bool = self.mergeTagsCheckBox.isChecked()
        config['reverse_order']: bool = self.reverseOrderCheckBox.isChecked()
        config['only_empty']: bool = self.onlyEmptyCheckBox.isChecked()

        mw.addonManager.writeConfig(__name__, config)
        self.accept()


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


config = get_config()
Browser.onMergeSelected = on_merge_selected
gui_hooks.browser_menus_did_init.append(on_browser_setup_menus)
