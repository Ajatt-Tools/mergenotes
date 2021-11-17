from typing import Iterable, Tuple

from aqt import mw
from aqt.qt import *

from .config import config, OrderingChoices, write_config


######################################################################
# UI Layout
######################################################################

class DialogUI(QDialog):
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
        self.fieldSeparatorLineEdit = QLineEdit()
        self.orderingComboBox = QComboBox()
        self.checkboxes = dict(self.create_checkboxes())
        self.bottom_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
        vbox.addWidget(self.bottom_box)
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
        for widget in self.checkboxes.values():
            vbox.addWidget(widget)
        return vbox

    def add_tooltips(self):
        self.fieldSeparatorLineEdit.setToolTip(
            "This string is inserted between the merged fields.\n"
            "Empty by default.\n"
            "Common options would be to change it to a single space: \" \",\n"
            "or to a linebreak: \"<br>\"."
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
            "Strip HTML tags from a pair of fields before performing a comparison."
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
        self.accept()
