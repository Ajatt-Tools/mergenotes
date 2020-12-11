from anki.notes import Note
from aqt import mw
from anki.lang import _
from aqt import gui_hooks
from aqt.qt import *
from aqt.utils import tooltip
from aqt.browser import Browser


######################################################################
# Utils
######################################################################

def getConfig() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__)
    cfg['delete_original_notes']: bool = cfg['delete_original_notes'] if 'delete_original_notes' in cfg else False
    cfg['merge_tags']: bool = cfg['merge_tags'] if 'merge_tags' in cfg else True
    cfg['reverse_order'] = cfg['reverse_order'] if 'reverse_order' in cfg else False
    cfg['field_separator']: str = cfg['field_separator'] if 'field_separator' in cfg else ""
    cfg['shortcut']: str = cfg['shortcut'] if 'shortcut' in cfg else "Ctrl+Alt+M"
    return cfg


def mergeTags(note1: Note, note2: Note) -> None:
    for tag in note2.tags:
        if tag == 'leech':
            continue
        if not note1.hasTag(tag):
            note1.addTag(tag)


def mergeFields(note1: Note, note2: Note) -> None:
    for (field_name, field_value) in note2.items():
        # don't waste cycles on empty fields
        # don't merge equal fields
        if field_value and field_name in note1 and note1[field_name] != note2[field_name]:
            note1[field_name] += config['field_separator'] + note2[field_name]


# Adds content of note2 to note1
def addSecondToFirst(note1: Note, note2: Note) -> None:
    mergeFields(note1, note2)

    if config['merge_tags'] is True:
        mergeTags(note1, note2)

    note1.flush()


# Col is a collection of cards, cids are the ids of the cards to merge
def mergeSelectedCardFields(cids: list) -> None:
    cards = [mw.col.getCard(cid) for cid in cids]
    # sort cards by their type, then by due number,
    # so that new cards are always in the beginning of the list,
    # mimicking the way cards are presented in the Anki Browser
    cards = sorted(cards, key=lambda card: (card.type, card.due), reverse=config['reverse_order'])
    notes = [card.note() for card in cards]

    # Iterate till 1st element and keep on decrementing i
    for i in reversed(range(len(cids) - 1)):
        addSecondToFirst(notes[i], notes[i + 1])

    if config['delete_original_notes'] is True:
        mw.col.remNotes([note.id for note in notes][1:])


def onBrowserMergeCards(browser: Browser) -> None:
    cids = browser.selectedCards()

    if len(cids) < 2:
        tooltip("At least two cards must be selected.")
        return

    browser.model.beginReset()
    browser.mw.checkpoint(_("Merge fields of selected cards"))

    mergeSelectedCardFields(cids)

    browser.model.endReset()
    browser.mw.reset()

    tooltip(f"{len(cids)} cards merged.", parent=browser)


def onMergeFieldsSettings() -> None:
    dialog = MergeFieldsSettingsWindow()
    dialog.exec_()


######################################################################
# UI Layout
######################################################################

class DialogUI(QDialog):
    def __init__(self):
        QDialog.__init__(self, parent=mw)
        self.fieldSeparatorLineEdit = QLineEdit()
        self.deleteOriginalNotesCheckBox = QCheckBox("Delete original notes")
        self.mergeTagsCheckBox = QCheckBox("Merge tags")
        self.reverseOrderCheckBox = QCheckBox("Reverse order")
        self.okButton = QPushButton("Ok")
        self.cancelButton = QPushButton("Cancel")
        self._setupUI()

    def _setupUI(self):
        self.setWindowTitle('Merge Fields Settings')
        self.setLayout(self.setupOuterLayout())
        self.addToolTips()

    def setupOuterLayout(self):
        vbox = QVBoxLayout()
        vbox.setSpacing(10)
        vbox.addLayout(self.createFieldSeparatorInputBox())
        vbox.addLayout(self.createCheckBoxGroup())
        vbox.addStretch(1)
        vbox.addLayout(self.createBottomGroup())
        return vbox

    def createFieldSeparatorInputBox(self):
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Field Separator:"))
        hbox.addWidget(self.fieldSeparatorLineEdit)
        return hbox

    def createCheckBoxGroup(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.deleteOriginalNotesCheckBox)
        vbox.addWidget(self.mergeTagsCheckBox)
        vbox.addWidget(self.reverseOrderCheckBox)
        return vbox

    def createBottomGroup(self):
        hbox = QHBoxLayout()
        hbox.addWidget(self.okButton)
        hbox.addWidget(self.cancelButton)
        hbox.addStretch()
        return hbox

    def addToolTips(self):
        pass  # TODO
        # .setToolTip()


######################################################################
# Settings window
######################################################################

class MergeFieldsSettingsWindow(DialogUI):
    def __init__(self):
        super().__init__()
        self.setDefaultValues()
        self.connectUIElements()

    def setDefaultValues(self):
        self.fieldSeparatorLineEdit.setText(config['field_separator'])
        self.deleteOriginalNotesCheckBox.setChecked(config['delete_original_notes'])
        self.mergeTagsCheckBox.setChecked(config['merge_tags'])
        self.reverseOrderCheckBox.setChecked(config['reverse_order'])

    def connectUIElements(self):
        self.okButton.clicked.connect(self.onConfirm)
        self.cancelButton.clicked.connect(self.close)

    def onConfirm(self):
        config['field_separator']: str = self.fieldSeparatorLineEdit.text()
        config['delete_original_notes']: bool = self.deleteOriginalNotesCheckBox.isChecked()
        config['merge_tags']: bool = self.mergeTagsCheckBox.isChecked()
        config['reverse_order']: bool = self.reverseOrderCheckBox.isChecked()
        mw.addonManager.writeConfig(__name__, config)
        self.close()


######################################################################
# Entry point
######################################################################


def setupContextMenu(browser: Browser) -> None:
    menu = browser.form.menu_Cards
    merge_fields_action = menu.addAction("Merge fields")
    merge_fields_action.setShortcut(QKeySequence(config['shortcut']))
    merge_fields_action.triggered.connect(browser.onBrowserMergeCards)


def setupEditMenu(browser: Browser) -> None:
    edit_menu = browser.form.menuEdit
    edit_menu.addSeparator()
    merge_fields_settings_action = edit_menu.addAction('Merge Fields Settings...')
    merge_fields_settings_action.triggered.connect(onMergeFieldsSettings)


def onBrowserSetupMenus(browser: Browser) -> None:
    setupContextMenu(browser)
    setupEditMenu(browser)


config = getConfig()
Browser.onBrowserMergeCards = onBrowserMergeCards
gui_hooks.browser_menus_did_init.append(onBrowserSetupMenus)
