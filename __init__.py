from anki.notes import Note
from aqt import mw
from anki.lang import _
from aqt import gui_hooks
from aqt.utils import tooltip
from aqt.browser import Browser


def addSecondToFirst(note1: Note, note2: Note) -> None:
    for (name, value) in note2.items():
        # don't waste cycles on empty fields
        if value and name in note1:
            note1[name] += note2[name]

    note1.flush()


# Col is a collection of cards, cids are the ids of the cards to merge
def mergeSelectedCardFields(cids: list) -> None:
    cards = [mw.col.getCard(cid) for cid in cids]
    cards = sorted(cards, key=lambda card: card.due)
    notes = [card.note() for card in cards]

    # Iterate till 1st element and keep on decrementing i
    for i in reversed(range(len(cids) - 1)):
        addSecondToFirst(notes[i], notes[i + 1])


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
    a.triggered.connect(self.onBrowserMergeCards)


Browser.onBrowserMergeCards = onBrowserMergeCards
gui_hooks.browser_menus_did_init.append(onBrowserSetupMenus)
