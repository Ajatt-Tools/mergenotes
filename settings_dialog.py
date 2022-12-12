# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Iterable

from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom

from .ajt_common import tweak_window, ShortCutGrabButton
from .config import config, OrderingChoices, write_config, fetch_config_toggleables


######################################################################
# UI Layout
######################################################################


class MonoSpaceLineEdit(QLineEdit):
    font_size = 14
    min_height = 32

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.font()
        font.setFamilies((
            "Noto Mono", "Noto Sans Mono", "DejaVu Sans Mono", "Droid Sans Mono",
            "Liberation Mono", "Courier New", "Courier", "Lucida", "Monaco", "Monospace",
        ))
        font.setPixelSize(self.font_size)
        self.setMinimumHeight(self.min_height)
        self.setFont(font)


def widgets_to_grid(widgets: Iterable[QWidget], columns: int = 2) -> Iterable[tuple[QWidget, int, int]]:
    row = col = 1
    for widget in widgets:
        yield widget, row, col
        if col < columns:
            col += 1
        else:
            row += 1
            col = 1


class DialogUI(QDialog):
    name = "Merge Fields Options"
    _checkbox_keys = tuple(fetch_config_toggleables())
    _shortcut_keys = (
        "merge_notes_shortcut",
        "duplicate_notes_shortcut",
    )

    def create_checkboxes(self) -> Iterable[tuple[str, QCheckBox]]:
        for key in self._checkbox_keys:
            yield key, QCheckBox(key.replace('_', ' ').capitalize())

    def __init__(self, *args, **kwargs):
        super().__init__(parent=mw, *args, **kwargs)
        self.setMinimumWidth(400)
        self.field_separator_edit = MonoSpaceLineEdit()
        self.punctuation_edit = MonoSpaceLineEdit()
        self.ordering_combo_box = QComboBox()
        self.shortcut_edits = {key: ShortCutGrabButton(config.get(key)) for key in self._shortcut_keys}
        self.checkboxes = dict(self.create_checkboxes())
        self.bottom_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(self.name)
        self.setLayout(self.setup_outer_layout())
        self.add_tooltips()

    def setup_outer_layout(self) -> QLayout:
        vbox = QVBoxLayout()
        vbox.setSpacing(10)
        vbox.addLayout(self.create_top_group())
        vbox.addLayout(self.create_checkbox_group())
        vbox.addStretch(1)
        vbox.addWidget(self.bottom_box)
        return vbox

    def create_top_group(self) -> QLayout:
        layout = QFormLayout()
        layout.addRow("Field Separator:", self.field_separator_edit)
        layout.addRow("Punctuation characters:", self.punctuation_edit)
        layout.addRow("Ordering:", self.ordering_combo_box)
        layout.addRow("Merge shortcut:", self.shortcut_edits['merge_notes_shortcut'])
        layout.addRow("Duplicate shortcut:", self.shortcut_edits['duplicate_notes_shortcut'])
        return layout

    def create_checkbox_group(self) -> QLayout:
        vbox = QGridLayout()
        for widget, row, col, in widgets_to_grid(self.checkboxes.values()):
            vbox.addWidget(widget, row, col)
        return vbox

    def add_tooltips(self):
        self.field_separator_edit.setToolTip(
            "This string is inserted between the merged fields.\n"
            "Empty by default.\n"
            "Common options would be to change it to a single space: \" \", or to a linebreak: \"<br>\".\n"
            r'You can use escaped characters like "\n" or "\t" to insert a linebreak or tab.'
        )
        self.punctuation_edit.setToolTip(
            "When comparing two fields, disregard the characters specified here.\n"
            "This makes it possible for two nearly equal fields to be successfully de-duplicated."
        )
        self.checkboxes['delete_original_notes'].setToolTip("Delete redundant notes after merging.")
        self.checkboxes['merge_tags'].setToolTip("Merge tags of selected notes in addition to contents of fields.")
        self.checkboxes['reverse_order'].setToolTip(
            "Sort cards in reverse.\n"
            "For Due ordering this would mean\n"
            "that a card with the biggest due number\n"
            "will receive the content of other selected cards."
        )
        self.checkboxes['only_empty'].setToolTip(
            "Copy only from non-empty fields to empty fields.\n"
            "If a field is already filled, no new text will be added to it."
        )
        self.checkboxes['html_agnostic_comparison'].setToolTip(
            "Strip HTML tags from a pair of fields before performing a comparison.\n"
            "Treat two fields equal if their text content matches, disregard HTML tags."
        )
        self.checkboxes['strip_punctuation_before_comparison'].setToolTip(
            "Remove characters specified in \"Punctuation characters\" before comparing two fields."
        )
        self.checkboxes['avoid_content_loss'].setToolTip(
            "Reorder notes so that notes with more common fields come last.\n"
            "Still, it is possible to lose content unless two notes have identical fields\n"
            "or belong to the same Note Type."
        )
        self.checkboxes['normalize_digits'].setToolTip(
            "Treat normal and full-width digit characters as equal."
        )
        self.checkboxes['apply_when_searching_duplicates'].setToolTip(
            "When using the \"Find Duplicates\" Anki feature,\n"
            "strip html tags, strip punctuation, and normalize digits before comparing fields,\n"
            "if each option is enabled respectfully."
            "This should yield more results."
        )
        self.checkboxes['show_duplicate_notes_button'].setToolTip(
            "Add \"Duplicate notes\" button to context menu of the Anki Browser."
        )


######################################################################
# Settings window
######################################################################

def uniq_char_str(text: str) -> str:
    return ''.join(set(text))


class MergeFieldsSettingsWindow(DialogUI):
    def __init__(self):
        super().__init__()
        self.populate_ordering_combobox()
        self.load_config_values()
        self.connect_ui_elements()
        tweak_window(self)
        restoreGeom(self, self.name)

    def populate_ordering_combobox(self):
        self.ordering_combo_box.addItems(OrderingChoices.as_list())

    def load_config_values(self):
        self.field_separator_edit.setText(config['field_separator'])
        self.punctuation_edit.setText(uniq_char_str(config['punctuation_characters']))
        self.ordering_combo_box.setCurrentText(config['ordering'])
        for key, widget in self.checkboxes.items():
            widget.setChecked(config[key])

    def connect_ui_elements(self):
        qconnect(self.bottom_box.accepted, self.accept)
        qconnect(self.bottom_box.rejected, self.reject)

    def accept(self):
        config['field_separator'] = self.field_separator_edit.text()
        config['punctuation_characters'] = uniq_char_str(self.punctuation_edit.text())
        config['ordering'] = self.ordering_combo_box.currentText()
        for key, widget in self.shortcut_edits.items():
            config[key] = widget.value()
        for key, widget in self.checkboxes.items():
            config[key] = widget.isChecked()
        write_config()
        return super().accept()

    def done(self, *args, **kwargs) -> None:
        saveGeom(self, self.name)
        return super().done(*args, **kwargs)


######################################################################
# Entry point
######################################################################


def on_open_settings() -> None:
    dialog = MergeFieldsSettingsWindow()
    dialog.exec()


def setup_mainwindow_menu():
    from .ajt_common import menu_root_entry

    root_menu = menu_root_entry()
    action = QAction(f"{MergeFieldsSettingsWindow.name}...", root_menu)
    qconnect(action.triggered, on_open_settings)
    root_menu.addAction(action)


def setup_edit_menu(browser: Browser) -> None:
    edit_menu = browser.form.menuEdit
    merge_fields_settings_action = edit_menu.addAction(f"{MergeFieldsSettingsWindow.name}...")
    qconnect(merge_fields_settings_action.triggered, on_open_settings)


def init():
    gui_hooks.browser_menus_did_init.append(setup_edit_menu)
    setup_mainwindow_menu()
