from aqt import mw
from aqt.qt import *

from .config import config, OrderingChoices, write_config


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

        write_config()
        self.accept()
