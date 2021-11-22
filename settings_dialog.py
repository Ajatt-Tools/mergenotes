from typing import Iterable, Tuple

from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom

from .ajt_common import tweak_window
from .config import config, OrderingChoices, write_config


######################################################################
# UI Layout
######################################################################

class DialogUI(QDialog):
    name = "Merge Fields Options"
    __checkbox_keys = (
        "delete_original_notes",
        "merge_tags",
        "reverse_order",
        "only_empty",
        "html_agnostic_comparison",
    )

    def create_checkboxes(self) -> Iterable[Tuple[str, QCheckBox]]:
        for key in self.__checkbox_keys:
            yield key, QCheckBox(key.replace('_', ' ').capitalize())

    def __init__(self, *args, **kwargs):
        super(DialogUI, self).__init__(parent=mw, *args, **kwargs)
        self.setMinimumWidth(320)
        self.fieldSeparatorLineEdit = QLineEdit()
        self.orderingComboBox = QComboBox()
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
        layout.addRow("Field Separator:", self.fieldSeparatorLineEdit)
        layout.addRow("Ordering:", self.orderingComboBox)
        return layout

    def create_checkbox_group(self):
        vbox = QVBoxLayout()
        for widget in self.checkboxes.values():
            vbox.addWidget(widget)
        return vbox

    def add_tooltips(self):
        self.fieldSeparatorLineEdit.setToolTip(
            "This string is inserted between the merged fields.\n"
            "Empty by default.\n"
            "Common options would be to change it to a single space: \" \",\n"
            "or to a linebreak: \"<br>\".\n"
            r'You can use escaped characters like "\n" or "\t" to insert a linebreak or tab.'
        )
        self.checkboxes['delete_original_notes'].setToolTip("Delete redundant notes after merging.")
        self.checkboxes['merge_tags'].setToolTip("Merge tags of selected notes in addition to contents of fields.")
        self.checkboxes['reverse_order'].setToolTip(
            "Sort cards in reverse.\n"
            "For Due ordering this would mean\n"
            "that a card with the biggest due number\n"
            "will receive the content of other selected cards."
        )
        self.checkboxes['only_empty'].setToolTip("Copy only from non-empty fields to empty fields.")
        self.checkboxes['html_agnostic_comparison'].setToolTip(
            "Strip HTML tags from a pair of fields before performing a comparison.\n"
            "Treat two fields equal if their text content matches, disregard HTML tags."
        )


######################################################################
# Settings window
######################################################################

class MergeFieldsSettingsWindow(DialogUI):
    def __init__(self):
        super().__init__()
        self.populate_ordering_combobox()
        self.load_config_values()
        self.connect_ui_elements()
        tweak_window(self)
        restoreGeom(self, self.name)

    def populate_ordering_combobox(self):
        self.orderingComboBox.addItems(OrderingChoices.as_list())

    def load_config_values(self):
        self.fieldSeparatorLineEdit.setText(config['field_separator'])
        self.orderingComboBox.setCurrentText(config['ordering'])
        for key, widget in self.checkboxes.items():
            widget.setChecked(config[key])

    def connect_ui_elements(self):
        qconnect(self.bottom_box.accepted, self.on_confirm)
        qconnect(self.bottom_box.rejected, self.reject)

    def on_confirm(self):
        config['field_separator']: str = self.fieldSeparatorLineEdit.text()
        config['ordering']: str = self.orderingComboBox.currentText()
        for key, widget in self.checkboxes.items():
            config[key] = widget.isChecked()
        write_config()
        saveGeom(self, self.name)
        self.accept()


######################################################################
# Entry point
######################################################################


def on_open_settings() -> None:
    dialog = MergeFieldsSettingsWindow()
    dialog.exec_()


def setup_mainwindow_menu():
    from .ajt_common import menu_root_entry

    root_menu = menu_root_entry()
    action = QAction(f"{MergeFieldsSettingsWindow.name}...", root_menu)
    action.triggered.connect(on_open_settings)
    root_menu.addAction(action)


def setup_edit_menu(browser: Browser) -> None:
    edit_menu = browser.form.menuEdit
    merge_fields_settings_action = edit_menu.addAction(f"{MergeFieldsSettingsWindow.name}...")
    qconnect(merge_fields_settings_action.triggered, on_open_settings)


def init():
    gui_hooks.browser_menus_did_init.append(setup_edit_menu)
    setup_mainwindow_menu()
