# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
from collections.abc import Iterable

from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom

from .ajt_common.consts import ADDON_SERIES
from .ajt_common.about_menu import menu_root_entry, tweak_window
from .ajt_common.anki_field_selector import AnkiFieldSelector, gather_all_field_names
from .ajt_common.grab_key import ShortCutGrabButton
from .ajt_common.monospace_line_edit import MonoSpaceLineEdit
from .ajt_common.multiple_choice_selector import MultipleChoiceSelector
from .ajt_common.widget_placement import place_widgets_in_grid
from .config import ACTION_NAME, ORDERING_CHOICES, Config, config

######################################################################
# UI Layout
######################################################################


def as_label(config_key: str) -> str:
    return config_key.replace("_", " ").capitalize()


def create_checkboxes() -> Iterable[tuple[str, QCheckBox]]:
    for key in config.bool_keys():
        yield key, QCheckBox(as_label(key))


class DialogUI(QDialog):
    name = f"{ACTION_NAME} Options"
    _shortcut_keys = (
        "merge_notes_shortcut",
        "duplicate_notes_shortcut",
    )
    _comparison_keys = (
        "ignore_html_tags",
        "ignore_punctuation",
        "full-width_as_half-width",
        "apply_when_searching_duplicates",
        "ignore_furigana",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(parent=mw, *args, **kwargs)
        self.setMinimumWidth(400)
        self._field_separator_edit = MonoSpaceLineEdit()
        self._punctuation_edit = MonoSpaceLineEdit()
        self._ordering_combo_box = QComboBox()
        self._custom_sort_field_edit = AnkiFieldSelector(self)
        self._shortcut_edits = {key: ShortCutGrabButton() for key in self._shortcut_keys}
        self._checkboxes = dict(create_checkboxes())
        self._limit_to_fields = MultipleChoiceSelector()
        self._bottom_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._reset_button = self._bottom_box.addButton("Restore defaults", QDialogButtonBox.ButtonRole.ResetRole)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(self.name)
        self.setLayout(self.setup_outer_layout())
        self.add_tooltips()

    def setup_outer_layout(self) -> QLayout:
        vbox = QVBoxLayout()
        vbox.setSpacing(10)
        vbox.addLayout(self.create_top_group())
        vbox.addWidget(self._limit_to_fields)
        vbox.addWidget(self.create_comparison_group())
        vbox.addWidget(self.create_behavior_group())
        vbox.addStretch(1)
        vbox.addWidget(self._bottom_box)
        return vbox

    def create_top_group(self) -> QLayout:
        layout = QFormLayout()
        layout.addRow("Field Separator:", self._field_separator_edit)
        layout.addRow("Punctuation characters:", self._punctuation_edit)
        layout.addRow("Ordering:", self._ordering_combo_box)
        layout.addRow("Custom sort field:", self._custom_sort_field_edit)
        layout.addRow("Merge shortcut:", self._shortcut_edits["merge_notes_shortcut"])
        layout.addRow("Duplicate shortcut:", self._shortcut_edits["duplicate_notes_shortcut"])
        return layout

    def create_comparison_group(self) -> QGroupBox:
        group = QGroupBox("Field comparison")
        group.setCheckable(False)
        group.setLayout(
            place_widgets_in_grid(self._checkboxes[key] for key in (self._checkboxes.keys() & self._comparison_keys))
        )
        return group

    def create_behavior_group(self) -> QGroupBox:
        group = QGroupBox("Behavior")
        group.setCheckable(False)
        group.setLayout(
            place_widgets_in_grid(self._checkboxes[key] for key in (self._checkboxes.keys() - self._comparison_keys))
        )
        return group

    def add_tooltips(self):
        self._field_separator_edit.setToolTip(
            "This string is inserted between the merged fields.\n"
            "Empty by default.\n"
            'Common options would be to change it to a single space: " ", or to a linebreak: "<br>".\n'
            r'You can use escaped characters like "\n" or "\t" to insert a linebreak or tab.'
        )
        self._punctuation_edit.setToolTip(
            "When comparing two fields, disregard the characters specified here.\n"
            "This makes it possible for two nearly equal fields to be successfully de-duplicated."
        )
        self._checkboxes["delete_original_notes"].setToolTip("Delete redundant notes after merging.")
        self._checkboxes["merge_tags"].setToolTip("Merge tags of selected notes in addition to contents of fields.")
        self._checkboxes["reverse_order"].setToolTip(
            "Sort cards in reverse.\n"
            "For Due ordering this would mean\n"
            "that a card with the smallest due number\n"
            "will receive the content of other selected cards."
        )
        self._checkboxes["skip_if_not_empty"].setToolTip(
            "Copy only from non-empty fields to empty fields.\n"
            "If a field is already filled, no new text will be added to it."
        )
        self._checkboxes["ignore_html_tags"].setToolTip(
            "Strip HTML tags from a pair of fields before performing a comparison.\n"
            "Treat two fields equal if their text content matches, disregard HTML tags."
        )
        self._checkboxes["ignore_punctuation"].setToolTip(
            'Remove characters specified in "Punctuation characters" before comparing two fields.'
        )
        self._checkboxes["avoid_content_loss"].setToolTip(
            "Reorder notes so that notes with more common fields come last.\n"
            "Still, it is possible to lose content unless two notes have identical fields\n"
            "or belong to the same Note Type."
        )
        self._checkboxes["full-width_as_half-width"].setToolTip("Treat normal and full-width characters as equal.")
        self._checkboxes["apply_when_searching_duplicates"].setToolTip(
            'When using the "Find Duplicates" Anki feature,\n'
            "strip html tags, strip punctuation, and normalize digits before comparing fields,\n"
            "if each option is enabled respectfully."
            "This should yield more results."
        )
        self._checkboxes["show_duplicate_notes_button"].setToolTip(
            'Add "Duplicate notes" button to context menu of the Anki Browser.'
        )
        self._checkboxes["ignore_furigana"].setToolTip(
            "Don't take furigana into account when comparing fields.\n"
            "Note that you may lose furigana when merging notes this way."
        )
        self._custom_sort_field_edit.setToolTip(
            'If Ordering is set to "Custom field", use contents of this field for sorting.'
        )
        self._ordering_combo_box.setToolTip(
            "How to sort cards when merging.\n"
            "If key is numeric, assume that the corresponding field contains a number."
        )


######################################################################
# Settings window
######################################################################


def uniq_char_str(text: str) -> str:
    return "".join(set(text))


class MergeFieldsSettingsWindow(DialogUI):
    def __init__(self):
        super().__init__()
        self.populate_widgets()
        self.load_config_values(config)
        self.connect_ui_elements()
        tweak_window(self)
        restoreGeom(self, self.name)

    def populate_widgets(self):
        self._ordering_combo_box.addItems(ORDERING_CHOICES.keys())
        self._limit_to_fields.set_texts(dict.fromkeys(gather_all_field_names()))

    def load_config_values(self, cfg: Config):
        self._field_separator_edit.setText(cfg["field_separator"])
        self._punctuation_edit.setText(uniq_char_str(cfg["punctuation_characters"]))
        self._ordering_combo_box.setCurrentText(cfg["ordering"])
        self._custom_sort_field_edit.setCurrentText(cfg["custom_sort_field"])
        self._limit_to_fields.set_checked_texts(cfg["limit_to_fields"])
        for key, widget in self._shortcut_edits.items():
            widget.setValue(cfg[key])
        for key, widget in self._checkboxes.items():
            widget.setChecked(cfg[key])

    def connect_ui_elements(self):
        qconnect(self._bottom_box.accepted, self.accept)
        qconnect(self._bottom_box.rejected, self.reject)
        qconnect(self._reset_button.clicked, functools.partial(self.load_config_values, Config.default()))
        qconnect(self._ordering_combo_box.currentIndexChanged, self._set_custom_field_active_status)

    def _set_custom_field_active_status(self):
        current_ordering = self._ordering_combo_box.currentText()
        self._custom_sort_field_edit.setEnabled(current_ordering.lower().startswith("custom field"))

    def accept(self):
        config["field_separator"] = self._field_separator_edit.text()
        config["punctuation_characters"] = uniq_char_str(self._punctuation_edit.text())
        config["ordering"] = self._ordering_combo_box.currentText()
        config["custom_sort_field"] = self._custom_sort_field_edit.currentText()
        config["limit_to_fields"] = self._limit_to_fields.checked_texts()
        for key, widget in self._shortcut_edits.items():
            config[key] = widget.value()
        for key, widget in self._checkboxes.items():
            config[key] = widget.isChecked()
        config.write_config()
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
    root_menu = menu_root_entry()
    action = QAction(f"{MergeFieldsSettingsWindow.name}...", root_menu)
    qconnect(action.triggered, on_open_settings)
    root_menu.addAction(action)


def setup_edit_menu(browser: Browser) -> None:
    edit_menu = browser.form.menuEdit
    merge_fields_settings_action = edit_menu.addAction(f"{ADDON_SERIES} {MergeFieldsSettingsWindow.name}...")
    qconnect(merge_fields_settings_action.triggered, on_open_settings)


def init():
    gui_hooks.browser_menus_did_init.append(setup_edit_menu)
    setup_mainwindow_menu()
