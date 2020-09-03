from aqt import mw
from aqt.qt import *
from anki.lang import _
from aqt import gui_hooks
from aqt.utils import tooltip
from aqt.browser import Browser

def addSecondToFirst(note1, note2):
    for (name, value) in note2.items():
        # don't wast cycles on empty fields
        if value and name in note1:
            note1[name] += note2[name]

    note1.flush()


# Col is a collection of cards, cids are the ids of the cards to merge
def mergeSelectedCardFields(cids):

    # Point i to the second last element in list
    i = len(cids) - 2

    # Iterate till 1st element and keep on decrementing i
    while i >= 0:
        card1 = mw.col.getCard(cids[i])
        note1 = card1.note()

        card2 = mw.col.getCard(cids[i + 1])
        note2 = card2.note()

        addSecondToFirst(note1, note2)

        i -= 1


def onBrowserMergeCards(self):
    cids = self.selectedCards()

    if len(cids) < 2:
        tooltip("At least two cards must be selected.")
        return

    self.model.beginReset()
    self.mw.checkpoint(_("Merge fields of selected cards"))

    mergeSelectedCardFields(cids)

    self.model.endReset()
    self.mw.reset()

    tooltip("{} cards merged.".format(len(cids)), parent=self)


def onBrowserSetupMenus(self):
    menu = self.form.menu_Cards
    a = menu.addAction("Merge fields")
    a.triggered.connect(self.onBrowserMergeCards)

Browser.onBrowserMergeCards = onBrowserMergeCards
gui_hooks.browser_menus_did_init.append(onBrowserSetupMenus)
