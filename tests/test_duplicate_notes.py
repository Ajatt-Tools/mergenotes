# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence
from unittest.mock import create_autospec

import pytest
from anki.cards import Card
from anki.notes import Note

from merge_notes import duplicate_notes
from merge_notes.duplicate_notes import ContextMenus, find_deck_id, n_gettext_duplicate
from playground.no_anki_config import NoAnkiConfigView
from tests.helpers import browser_with_cards_menu


class TestDuplicateNotes:
    """Verify duplicate-note status text and destination deck selection."""

    @pytest.mark.parametrize(
        "n_notes,is_done,expected",
        [
            (1, False, "Duplicate 1 note"),
            (2, False, "Duplicate 2 notes"),
            (1, True, "Duplicated 1 note"),
            (3, True, "Duplicated 3 notes"),
        ],
    )
    def test_status_text(self, n_notes: int, is_done: bool, expected: str) -> None:
        """Pluralize pending and completed duplicate operations."""
        assert n_gettext_duplicate(n_notes, is_done) == expected

    @pytest.mark.parametrize("did,odid,expected", [(5, 0, 5), (5, 7, 7)])
    def test_find_deck_id(self, did: int, odid: int, expected: int) -> None:
        """Prefer the original deck when the first card is in a filtered deck."""
        card = create_autospec(Card, instance=True)
        card.did, card.odid = did, odid
        note = create_autospec(Note, instance=True)
        note.cards.return_value = [card]
        assert find_deck_id(note) == expected


class TestDuplicateContextMenu:
    """Exercise real Qt actions rather than duplicating Qt signal behavior in fakes.

    QAction.triggered emits a checked flag that the menu adapter must discard before forwarding the browser.
    https://doc.qt.io/qt-6/qaction.html#triggered
    """

    @pytest.mark.parametrize("show_button,expected_labels", [(True, ["Duplicate notes"]), (False, [])])
    def test_visibility(
        self, no_anki_config: NoAnkiConfigView, show_button: bool, expected_labels: Sequence[str]
    ) -> None:
        """Only add the duplicate action when its configuration flag is enabled."""
        no_anki_config["show_duplicate_notes_button"] = show_button
        browser = browser_with_cards_menu()
        ContextMenus(no_anki_config).setup_context_menu(browser)
        assert [action.text() for action in browser.form.menu_Cards.actions()] == expected_labels

    @pytest.mark.parametrize("shortcut", ["Ctrl+Alt+D", ""])
    def test_shortcut_and_callback(
        self, monkeypatch: pytest.MonkeyPatch, no_anki_config: NoAnkiConfigView, shortcut: str
    ) -> None:
        """Keep empty shortcuts unassigned and forward the originating browser on trigger."""
        no_anki_config["show_duplicate_notes_button"] = True
        no_anki_config["duplicate_notes_shortcut"] = shortcut
        browser = browser_with_cards_menu()
        ContextMenus(no_anki_config).setup_context_menu(browser)
        action = browser.form.menu_Cards.actions()[0]
        assert action.shortcut().toString() == shortcut
        duplicate = create_autospec(duplicate_notes.duplicate_notes)
        monkeypatch.setattr(duplicate_notes, "duplicate_notes", duplicate)
        action.trigger()
        duplicate.assert_called_once_with(browser)
