from anki.notes import Note
from aqt import mw
from anki.lang import _
from aqt import gui_hooks, QKeySequence
from aqt.utils import tooltip
from aqt.browser import Browser


def getConfig() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__)
    cfg['delete_original_notes']: bool = cfg['delete_original_notes'] if 'delete_original_notes' in cfg else False
    cfg['field_separator']: str = cfg['field_separator'] if 'field_separator' in cfg else ""
    cfg['shortcut']: str = cfg['shortcut'] if 'shortcut' in cfg else "Ctrl+Alt+M"
    return cfg

def addSecondToFirst(note1: Note, note2: Note) -> None:
    for (name, value) in note2.items():
        # don't waste cycles on empty fields
        # don't merge equal fields
        if value and name in note1 and note1[name] != note2[name]:
            note1[name] += config['field_separator'] + note2[name]

    for tag in note2.tags:
        if not note1.hasTag(tag):
            note1.addTag(tag)

    note1.flush()


# Col is a collection of cards, cids are the ids of the cards to merge
def mergeSelectedCardFields(cids: list) -> None:
    cards = [mw.col.getCard(cid) for cid in cids]
    cards = sorted(cards, key=lambda card: card.due)
    notes = [card.note() for card in cards]

    # Iterate till 1st element and keep on decrementing i
    for i in reversed(range(len(cids) - 1)):
        addSecondToFirst(notes[i], notes[i + 1])

    if config['delete_original_notes']:
        mw.col.remNotes(list(set([note.id for note in notes[1:]])))


def onBrowserMergeCards(self) -> None:
    cids = self.selectedCards()

    if len(cids) < 2:
        tooltip("At least two cards must be selected.")
        return

    self.model.beginReset()
    self.mw.checkpoint(_("Merge fields of selected cards"))

    mergeSelectedCardFields(cids)

    self.model.endReset()
    self.mw.reset()

    tooltip(f"{len(cids)} cards merged.", parent=self)


def onBrowserSetupMenus(self) -> None:
    menu = self.form.menu_Cards
    a = menu.addAction("Merge fields")
    a.setShortcut(QKeySequence(config['shortcut']))
    a.triggered.connect(self.onBrowserMergeCards)


config = getConfig()
Browser.onBrowserMergeCards = onBrowserMergeCards
gui_hooks.browser_menus_did_init.append(onBrowserSetupMenus)
